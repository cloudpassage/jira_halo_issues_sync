import cloudpassage
import os
from logger import Logger
import re
from multiprocessing.dummy import Pool as ThreadPool


class Halo(object):
    def __init__(self, key, secret, api_host):
        """Instantiate with key, secret, and API host.

        Args:
            key (str): Halo API key.
            secret (str): Halo API secret.
            api_host (str): Hostname for CloudPassage API.
        """
        self.logger = Logger()
        integration = self.get_integration_string()
        self.session = cloudpassage.HaloSession(key, secret, api_host=api_host,
                                                integration_string=integration)
        self.issues = cloudpassage.Issue(self.session)
        self.http_helper = cloudpassage.HttpHelper(self.session)
        try:
            self.session.authenticate_client()
        except cloudpassage.CloudPassageAuthentication as e:
            self.logger.critical("\nBad Halo API credentials!\n")
            raise e
        return

    def describe_all_issues(self, timestamp, critical_only=True):
        """Return list of all isssues since timestamp, described.

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
        all_issue_ids = {x["id"] for x in
                         self.get_issues_touched_since(timestamp,
                                                       critical_only)}
        issue_getter = self.get_issue_full
        # Enrich them all, 10 threads wide
        pool = ThreadPool(10)
        results = pool.map(issue_getter, list(all_issue_ids))
        pool.close()
        pool.join()
        return results

    def describe_asset(self, asset_type, asset_id):
        """Get full json description of asset."""
        supported_assets = {"server": cloudpassage.Server}
        try:
            asset_obj = supported_assets[asset_type](self.session)
            return asset_obj.describe(asset_id)
        except KeyError:
            msg = "Unsupported asset type: {}".format(asset_type)
            self.logger.error(msg)
            return {}

    def describe_finding(self, finding_url):
        """Wrap functionality to get findings for scan and event findings."""
        if "/scans/" in finding_url:
            scan_id, finding_id = self.parse_finding_url(finding_url)
            result = self.get_finding(scan_id, finding_id)
        elif "/events/" in finding_url:
            event_id = finding_url.split('/')[-1]
            h_h = cloudpassage.http_helper(self.session)
            result = h_h.get("/v1/events/{}".format(event_id))
        else:
            msg = "Unable to determine finding type: {}".format(finding_url)
            self.logger.error(msg)
            result = None
        return result

    def get_finding(self, scan_id, finding_id):
        """Get finding for finding_id from scan_id."""
        url = "/v1/scans/{}/findings/{}".format(scan_id, finding_id)
        return self.http_helper.get(url)

    def get_integration_string(self):
        """Return integration string for this tool."""
        return "Jira-Halo-Issues-Sync/%s" % self.get_tool_version()

    def get_issue_full(self, issue_id):
        """Get entire issue body."""
        return self.issues.describe(issue_id)

    def get_issues_touched_since(self, timestamp, critical_only=True):
        """Return all issues created,resolved, or last seen since timestamp.

        Args:
            timestamp (str): ISO8601-formatted timestamp. All issues created,
                resolved, or last seen since this datestamp will be retrieved
                from the CloudPassage Halo API.

        Returns:
            dict
        """
        updated_params = {"status": "active",
                          "state": "active,inactive,missing,retired",
                          "updated_at_gte": timestamp}
        resolved_params = {'status': 'resolved',
                           'resolved_at_gte': timestamp,
                           'state': 'active,inactive,missing,retired'}
        if critical_only:
            updated_params["critical"] = "true"
            resolved_params["critical"] = "true"
        updated = self.http_helper.get_paginated("/v1/issues", "issues",
                                                 99, params=updated_params)
        resolved = self.http_helper.get_paginated("/v1/issues", "issues",
                                                  99, params=resolved_params)
        all_issues = resolved + updated
        # Ensure time filtering works
        issues_filtered = [x for x in all_issues if
                           self.targeted_date(x["last_seen_at"], timestamp)]
        bad = len(all_issues) - len(issues_filtered)
        msg = "Discarding {} issues outside of time range".format(bad)
        self.logger.debug(msg)
        # Deduplicate
        issues_final = self.deduplicate_issues(issues_filtered)
        return issues_final

    @classmethod
    def deduplicate_issues(cls, issues):
        all_issue_ids = set([])
        issues_final = []
        for x in issues:
            if x["id"] in all_issue_ids:
                continue
            all_issue_ids.add(x["id"])
            issues_final.append(x)
        return issues_final

    @classmethod
    def targeted_date(cls, sample, target):
        if sample > target:
            return True
        return False

    def get_tool_version(self):
        """Get version of this tool from the __init__.py file."""
        here_path = os.path.abspath(os.path.dirname(__file__))
        init_file = os.path.join(here_path, "__init__.py")
        ver = 0
        with open(init_file, 'r') as i_f:
            rx_compiled = re.compile(r"\s*__version__\s*=\s*\"(\S+)\"")
            ver = rx_compiled.search(i_f.read()).group(1)
        return ver

    def parse_finding_url(self, url):
        """Return scan_id and finding_id from finding url.

        Args:
            url (str): Finding URL.

        Returns:
            tuple (scan_id, finding_id) or None, if no match.
        """
        rx = r"^https://\w+\.cloudpassage\.com/v\d/scans/[A-Za-z0-9]+/findings/[A-Za-z0-9]+$"  # NOQA
        if not re.match(rx, url):
            self.logger.error("Unable to parse finding URL: {}".format(url))
            return None
        else:
            rxtractor = r".*/scans/(?P<scan_id>[A-Za-z0-9]+)/findings/(?P<finding_id>[A-Za-z0-9]+)"  # NOQA
            result = re.search(rxtractor, url)
            scan_id, finding_id = (result.group("scan_id"),
                                   result.group("finding_id"))
        return (scan_id, finding_id)
