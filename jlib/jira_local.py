from jira import JIRA
from jira.exceptions import JIRAError
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

from .logger import Logger
from .mapper import map_fields
from .formatter import Formatter


class JiraLocal(object):
    def __init__(self, jira_url, auth_user, auth_token, jira_config, jira_fields_dict):
        self.jira_instance = JIRA(jira_url, basic_auth=(auth_user, auth_token))
        self.jira_config = jira_config
        self.jira_fields_dict = jira_fields_dict
        self.jira_issue_id_field_key = jira_fields_dict[jira_config["jira_issue_id_field"]]
        self.log = Logger()
        return

    def get_jira_issues(self, project_key, halo_issues):
        jira_issues_dict = {}
        with ThreadPoolExecutor(max_workers=os.cpu_count()*4) as executor:
            future_to_issue_id = {
                executor.submit(
                    self.get_jira_issues_for_halo_issue, issue["id"], project_key
                ): issue["id"] for issue in halo_issues
            }
            for future in as_completed(future_to_issue_id):
                issue_id = future_to_issue_id[future]
                jira_issues = future.result()
                jira_issues_dict[issue_id] = jira_issues
        return jira_issues_dict

    def get_jira_epics_or_issues(self, project_keys, issuetype, dict_format=True):
        if isinstance(project_keys, str):
            project_keys = [project_keys]
        jira_issues_dict = defaultdict(list)
        jira_issues = self.jira_instance.search_issues(
            f'project in ({", ".join(x for x in project_keys)}) AND '
            f'resolution = Unresolved AND '
            f'issuetype={issuetype} AND '
            f'"{self.jira_config["jira_issue_id_field"]}" is not EMPTY',
            maxResults=False
        )
        if not dict_format:
            return jira_issues
        for issue in jira_issues:
            jira_issues_dict[issue.raw["fields"][self.jira_issue_id_field_key]].append(issue)
        return jira_issues_dict

    def get_jira_issues_for_halo_issue(self, issue_id, project_key):
        results = self.jira_instance.search_issues(
            f'project="{project_key}" AND '
            f'"{self.jira_config["jira_issue_id_field"]}"~{issue_id} AND '
            f'issuetype="{self.jira_config["jira_issue_type"]}"'
        )
        return results

    def create_jira_epic(self, group_key_hash, group_key_str, project_key):
        # Get IDs for epic fields
        epic_dict = {
            'project': {'key': project_key},
            'summary': group_key_str,
            self.jira_fields_dict["Epic Name"]: group_key_str,
            'description': group_key_str,
            'issuetype': {'name': 'Epic'},
            self.jira_issue_id_field_key: group_key_hash
        }
        epic = self.jira_instance.create_issue(fields=epic_dict)
        return epic

    def create_jira_issue(self, issue, epic, jira_fields_dict, fields, project_key):
        epic_link = None
        if epic:
            epic_link = epic.key

        summary, description, field_mapping = self.prepare_issue(issue, fields, jira_fields_dict)

        issue_dict = {
            'project': {'key': project_key},
            'issuetype': {'name': self.jira_config['jira_issue_type']},
            self.jira_issue_id_field_key: issue["id"],
            self.jira_fields_dict["Epic Link"]: epic_link,
            'summary': summary,
            'description': description
        }

        issue_dict.update(field_mapping)
        self.log.info(f"Creating issue: {issue['id']}")
        self.jira_instance.create_issue(fields=issue_dict)

    def update_jira_issue(self, issue, jira_issues, jira_fields_dict, fields):
        self.log.info(f"Updating issue: {issue['id']}")
        for jira_issue in jira_issues:
            summary, description, field_mapping = self.prepare_issue(issue, fields, jira_fields_dict)
            issue_dict = {
                'summary': summary,
                'description': description
            }
            issue_dict.update(field_mapping)
            jira_issue.update(fields=issue_dict)
            if issue["status"] == "resolved":
                self.transition_issue(jira_issue, self.jira_config["issue_status_closed"])
            elif jira_issue.raw["fields"]["status"]["name"] == self.jira_config["issue_status_closed"]:
                self.transition_issue(jira_issue, self.jira_config["issue_status_reopened"])

    def transition_issue(self, issue, transition_name):
        self.log.info(f"Transitioning issue {issue.key} to {transition_name}")
        transition_id = self.jira_instance.find_transitionid_by_name(issue, transition_name)
        try:
            self.jira_instance.transition_issue(issue, transition_id)
        except JIRAError:
            self.log.error(
                f"Could not transition Jira Issue '{issue.key}' "
                f"from {issue.raw['fields']['status']['name']} to {transition_name}"
            )

    def prepare_issue(self, issue, fields, jira_fields_dict):
        asset_formatted = Formatter.format_object(issue["asset_type"], issue.pop("asset"))
        finding_formatted = Formatter.format_object("findings", issue.pop("findings"))
        issue_formatted = Formatter.format_object("issue", issue)

        summary = Formatter.format_summary(issue)
        description = issue_formatted + asset_formatted + finding_formatted
        description = description[:32759] + '{code}\n\n'

        dynamic_map = fields.get("mapping") or {}
        static = fields.get("static") or {}
        field_mapping = map_fields(dynamic_map, static, issue, jira_fields_dict)

        return summary, description, field_mapping

    def push_issues(self, issues, jira_epics_dict, jira_issues_dict, jira_fields_dict, fields, project_key=None):
        with ThreadPoolExecutor(max_workers=os.cpu_count() * 4) as executor:
            for issue in issues:
                jira_issues = jira_issues_dict.get(issue["id"])
                if jira_issues:
                    executor.submit(self.update_jira_issue, issue, jira_issues, jira_fields_dict, fields)
                else:
                    groupby_key = issue.pop("groupby_key", "")
                    epic = jira_epics_dict.get(groupby_key)
                    executor.submit(self.create_jira_issue, issue, epic, jira_fields_dict, fields, project_key)

    def cleanup_epics(self, project_keys):
        jira_issues = self.get_jira_epics_or_issues(
            project_keys, self.jira_config["jira_issue_type"], dict_format=False)
        epics_set = set(issue.raw["fields"][self.jira_fields_dict["Epic Link"]] for issue in jira_issues)
        jira_epics = self.get_jira_epics_or_issues(project_keys, "Epic", dict_format=False)

        with ThreadPoolExecutor(max_workers=os.cpu_count() * 4) as executor:
            for epic in jira_epics:
                if epic.key not in epics_set:
                    self.log.info(f"Deleting epic: {epic.key}")
                    executor.submit(self.transition_issue, epic, self.jira_config["issue_status_closed"])
