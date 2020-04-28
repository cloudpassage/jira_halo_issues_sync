import os
import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pprint import pprint

import cloudpassage

from .logger import Logger


class Halo(object):
    def __init__(self, key, secret, api_host):
        """Instantiate with key, secret, and API host.

        Args:
            config (ConfigHelper): Config Object
        """
        self.logger = Logger()
        integration = self.get_integration_string()
        self.session = cloudpassage.HaloSession(key, secret, api_host=api_host, integration_string=integration)
        self.issue = cloudpassage.Issue(self.session, endpoint_version=3)
        self.http_helper = cloudpassage.HttpHelper(self.session)
        self.cve_detail = cloudpassage.CveDetails(self.session)

    def get_issues(self, filters):
        """Return list of all issues since timestamp, described.

        This wraps the initial retrieval of all issues touched since timestamp,
        and makes multi-threaded calls to self.get_issue_full() to get the
        full description of all issues.

        Args:
            timestamp (str): ISO8601-formatted timestamp.

        Returns:
            list: List of dictionary objects describing all issues since
                timestamp.
        """
        # Create a set of all issue IDs in scope for this run of the tool.
        issue_filters = filters.get("issue") or {}
        if "csp_tags" in issue_filters:
            csp_tags = issue_filters["csp_tags"]
            csp_tags_formatted = re.sub('[{}]', '', json.dumps(csp_tags).replace(' ', ''))
            issue_filters["csp_tags"] = csp_tags_formatted

        filtered_issues = self.issue.list_all(**issue_filters)

        if filtered_issues:
            self.logger.info(f"Issues to process: {len(filtered_issues)}")
            filtered_issues = self.get_asset_and_findings(filtered_issues)
            filtered_issues = self.get_cve_details(filtered_issues)

        return filtered_issues

    def get_asset_and_findings(self, issues):
        with ThreadPoolExecutor(max_workers=os.cpu_count() * 2) as executor:
            asset_future_to_issue = {
                executor.submit(self.describe, issue["asset_url"]): issue for issue in issues
            }
            findings_future_to_issue = {
                executor.submit(self.describe, issue["last_finding_urls"][-1]):
                    issue for issue in issues if "last_finding_urls" in issue
            }
            self.enrich_issues(asset_future_to_issue, 'asset')
            self.enrich_issues(findings_future_to_issue, 'findings')
            return issues

    def get_cve_details(self, issues):
        with ThreadPoolExecutor(max_workers=os.cpu_count() * 2) as executor:
            cve_ids = set(cve for issue in issues for cve in issue.get("cve_ids", []))
            cve_future_to_cve = {executor.submit(self.cve_detail.describe, cve_id): cve_id for cve_id in cve_ids}
            cve_dict = self.get_cve_dict(cve_future_to_cve)
            pprint(cve_dict)
            for issue in issues:
                if issue["extended_attributes"] and "cve_info" in issue["extended_attributes"]:
                    for cve in issue["extended_attributes"]["cve_info"]:
                        try:
                            del cve_dict[cve["id"]]["Vulnerable packages"]
                        except KeyError:
                            pass
                        cve["detail"] = cve_dict[cve["id"]]
            return issues

    def get_cve_dict(self, cve_future_to_cve):
        cve_dict = {}
        for future in as_completed(cve_future_to_cve):
            cve_id = cve_future_to_cve[future]
            try:
                cve_detail = future.result()
                cve_dict[cve_id] = cve_detail
            except Exception as e:
                self.logger.error(f"{cve_id} generated an exception: {e}")
        return cve_dict

    def enrich_issues(self, future_to_issue, type):
        for future in as_completed(future_to_issue):
            issue = future_to_issue[future]
            try:
                data = future.result()
            except Exception as e:
                self.logger.error(f"{issue['asset_url']} generated an exception: {e}")
            issue[type] = data

    def describe(self, url):
        """Get full json description of asset or finding."""
        try:
            short_url = '/' + url.split('/', 3)[-1]
            object_type = url.split('/')[-2][:-1]
        except IndexError:
            self.logger.error("Invalid URL:" + url)
            return None

        try:
            response = self.http_helper.get(short_url)
        except cloudpassage.exceptions.CloudPassageBaseException:
            self.logger.error("Invalid URL: " + url)
            pass
        if object_type in response:
            return response[object_type]
        else:
            return response

    def get_integration_string(self):
        """Return integration string for this tool."""
        return "Jira-Halo-Issues-Sync/%s" % self.get_tool_version()

    @staticmethod
    def get_tool_version():
        """Get version of this tool from the __init__.py file."""
        here_path = os.path.abspath(os.path.dirname(__file__))
        init_file = os.path.join(here_path, "__init__.py")
        ver = 0
        with open(init_file, 'r') as i_f:
            rx_compiled = re.compile(r"\s*__version__\s*=\s*\"(\S+)\"")
            ver = rx_compiled.search(i_f.read()).group(1)
        return ver
