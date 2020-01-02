import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from operator import itemgetter

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
        csp_tag_filters = []
        if "csp_tags" in issue_filters:
            csp_tag_filters = filters["issue"]["csp_tags"]
            del issue_filters["csp_tags"]

        all_issues = self.issue.list_all(**issue_filters)

        filtered_issues = self.filter_issues(all_issues, "csp_tags", csp_tag_filters)
        if filtered_issues:
            self.logger.info(f"Issues to process: {len(filtered_issues)}")
            filtered_issues = self.get_asset_and_findings(filtered_issues)

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

    @staticmethod
    def filter_issues(issues, field, csp_tag_filters):
        if not issues:
            return
        issues_filtered = [
            x for x in issues if all(csp_tag in x.get(field, []) for csp_tag in csp_tag_filters)
        ]
        return issues_filtered

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
