"""Reconcile Halo issues against Jira."""
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from cloudpassage.exceptions import CloudPassageResourceExistence
from itertools import groupby
import json
import hashlib
from jlib.halo import Halo
from jlib.jira_local import JiraLocal
from jlib.logger import Logger


class Reconciler(object):
    """Reconcile issues between Halo and Jira.
    Args:
        halo (obj): Instance of jlib.Halo()
        jira (obj): Instance of jlib.JiraLocal()
        dynamic_mapping (dict): Dictionary describing dynamic field mapping
            from Halo to Jira. See README.md for details.
        static_mapping (dict): Statically-defined fields for Jira. See
            README.md for more info.
    """

    def __init__(self, config, rule):
        self.logger = Logger()
        self.config = config
        self.halo = Halo(config.halo_api_key, config.halo_api_secret_key, config.halo_api_hostname)
        self.jira = JiraLocal(config.jira_api_url, config.jira_api_user, config.jira_api_token, rule,
                              config.jira_fields_dict)
        self.rule = rule

    def reconcile_issues(self, halo_issues, project_key):
        jira_issues_dict = self.jira.get_jira_issues(project_key, halo_issues)
        jira_epics_dict = self.jira.get_jira_epics_or_issues(project_key, "Epic")
        issues_with_gk = []
        futures_to_group_key = {}
        groupby_params = self.rule.get("groupby", [])
        sorted_issues = sorted(halo_issues, key=lambda issue: [issue[x] for x in groupby_params])
        with ThreadPoolExecutor(max_workers=os.cpu_count()*2) as executor:
            for group_key, issues_group in groupby(
                    sorted_issues, key=lambda issue: {x: issue[x] for x in groupby_params}):
                group_key_hash = ""
                if group_key:
                    group_key_str = json.dumps(group_key)
                    group_key_hash = hashlib.sha256(group_key_str.encode()).hexdigest()
                    if group_key_hash not in jira_epics_dict:
                        futures_to_group_key[executor.submit(
                            self.jira.create_jira_epic, group_key_hash, group_key_str, project_key
                        )] = group_key_hash

                for issue in issues_group:
                    issue["groupby_key"] = group_key_hash
                    issues_with_gk.append(issue)
            for future in as_completed(futures_to_group_key):
                jira_epics_dict[futures_to_group_key[future]] = future.result()
        
        fields = self.rule.get("fields") or {}
        self.jira.push_issues(
            issues_with_gk,
            jira_epics_dict,
            jira_issues_dict,
            self.config.jira_fields_dict,
            fields,
            project_key
        )

    def get_jira_halo_issues(self, jira_issues_dict):
        issues = []
        with ThreadPoolExecutor(max_workers=os.cpu_count()*2) as executor:
            futures = [executor.submit(self.halo.issue.describe, issue_id) for issue_id in jira_issues_dict]
            for future in as_completed(futures):
                try:
                    issues.append(future.result()["issue"])
                except (CloudPassageResourceExistence, KeyError):
                    pass
        return issues

    def update_all_jira_issues(self):
        jira_issues_dict = self.jira.get_jira_epics_or_issues(
            self.rule["jira_config"]["project_keys"],
            self.rule["jira_config"]["jira_issue_type"]
        )
        jira_epics_dict = {}
        fields = self.rule.get("fields") or {}
        halo_issues = self.get_jira_halo_issues(jira_issues_dict)
        if halo_issues:
            self.logger.info(f"Updating {len(halo_issues)} active Jira issues")
            halo_issues = self.halo.get_asset_and_findings(halo_issues)
            halo_issues = self.halo.get_cve_details(halo_issues)
            self.jira.push_issues(
                halo_issues,
                jira_epics_dict,
                jira_issues_dict,
                self.config.jira_fields_dict,
                fields
            )

    def cleanup(self, project_keys):
        self.jira.cleanup_epics(project_keys)
