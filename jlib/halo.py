import os
import re
from multiprocessing.dummy import Pool as ThreadPool
from operator import itemgetter

import cloudpassage

from .logger import Logger


class Halo(object):
    def __init__(self, key, secret, api_host, describe_issues_threads,
                 issue_sync_max=0):
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
        self.issues = cloudpassage.Issue(self.session, endpoint_version=3)
        self.http_helper = cloudpassage.HttpHelper(self.session)
        try:
            self.session.authenticate_client()
        except cloudpassage.CloudPassageAuthentication as e:
            self.logger.critical("\nBad Halo API credentials!\n")
            raise e
        self.describe_issues_threads = describe_issues_threads
        if issue_sync_max != 0:
            self.issue_sync_max = issue_sync_max
        else:
            self.issue_sync_max = 2000
        return

    def describe_all_issues(self, timestamp, critical_only=True, **kwargs):
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
        # Create a list of issue types to suppress
        suppressed_types = []
        if "no_sva" in kwargs and kwargs["no_sva"] is True:
            suppressed_types.append("sva")
            msg = "Not retrieving SVA issues (config item ${NO_SVA} is True)"
            self.logger.info(msg)
        # Create a set of all issue IDs in scope for this run of the tool.
        all_issue_ids = {x["id"] for x in
                         self.get_issues_touched_since(timestamp,
                                                       critical_only)}
        issue_getter = self.get_issue_full
        msg = "Describing all Halo issues. Concurrency: {}".format(str(self.describe_issues_threads))  # NOQA
        self.logger.debug(msg)
        # Enrich them all, 10 threads wide
        pool = ThreadPool(self.describe_issues_threads)
        results = pool.map(issue_getter, list(all_issue_ids))
        pool.close()
        pool.join()
        results_cleaned = [x['issue'] for x in results if x is not None]
        retval = [self.time_label_issue(x) for x in results_cleaned
                  if x["type"] not in suppressed_types]
        if len(retval) != len(results):
            msg = "Of {} issues, {} are not filtered out.".format(len(results),
                                                                  len(retval))
            self.logger.info(msg)
        return retval

    def describe(self, url):
        """Get full json description of asset."""
        h_h = cloudpassage.HttpHelper(self.session)
        try:
            short_url = '/' + '/'.join(url.split('/')[3:])
            object_type = url.split('/')[3:][-2][:-1]
        except IndexError:
            self.logger.error("Invalid URL:" + url)
            return None

        response = None
        try:
            response = h_h.get(short_url)
        except cloudpassage.exceptions.CloudPassageBaseException:
            self.logger.error("Invalid URL: " + url)
            pass
        if object_type in response:
            result = response[object_type]
        else:
            result = response
        return result

    def get_integration_string(self):
        """Return integration string for this tool."""
        return "Jira-Halo-Issues-Sync/%s" % self.get_tool_version()

    def get_issue_full(self, issue_id):
        """Get entire issue body."""
        try:
            return self.issues.describe(issue_id)
        except cloudpassage.CloudPassageResourceExistence:
            return None

    def get_issues_touched_since(self, timestamp, critical_only=True):
        """Return all issues created,resolved, or last seen since timestamp.

        Args:
            timestamp (str): ISO8601-formatted timestamp. All issues created,
                resolved, or last seen since this datestamp will be retrieved
                from the CloudPassage Halo API.

        Returns:
            dict
        """
        if critical_only:
            all_issues = self.issues.list_all(
                critical=True,
                state="active,deactivated,missing,retired",
                since=timestamp)
        else:
            all_issues = self.issues.list_all(
                state="active,deactivated,missing,retired",
                since=timestamp)
        msg = "Issues to process: {}".format(len(all_issues))
        self.logger.info(msg)
        labeled = [self.time_label_issue(x) for x in all_issues]
        # Ensure time filtering works
        issues_filtered = [x for x in labeled if
                           self.targeted_date(x["tstamp"], timestamp)]
        discarded_issues = [x for x in labeled if not
                            self.targeted_date(x["tstamp"], timestamp)]
        bad = len(labeled) - len(issues_filtered)
        msg = "Discarding {} issues outside of time range".format(bad)
        if bad != 0:
            self.logger.info(msg)
        for d_i in discarded_issues:
            msg = ("Issue out of tmie range (discarding): ID: {} Timestamp: "
                   "{}".format(d_i["id"], d_i["tstamp"]))
            self.logger.debug(msg)
        # Deduplicate
        issues_dedup = self.deduplicate_issues(issues_filtered)
        issues_time_sorted = [x for x in sorted(issues_dedup,
                                                key=itemgetter("tstamp"))]
        issues_final = issues_time_sorted[:self.issue_sync_max]
        limit_discarded = len(issues_time_sorted) - len(issues_final)
        msg = ("Limiting sync to {} issues, discarding {} of "
               "{}").format(self.issue_sync_max, limit_discarded,
                            len(issues_time_sorted))
        if limit_discarded:
            self.logger.warn(msg)
        else:
            self.logger.debug(msg)
        return issues_final

    @classmethod
    def time_label_issue(cls, issue):
        """Return a copy of the `issue` arg (dict) with added `tstamp` field.

        The tstamp field is determined by taking the most recent timestamp
        from the issue, by looking at created_at, last_seen_at, and
        resolved_at.

        """
        target_fields = ["created_at", "resolved_at", "last_seen_at", "updated_at"]
        tstamps = [issue[x] for x in target_fields if x in issue and issue[x] is not None]
        retval = issue.copy()
        retval["tstamp"] = sorted(tstamps)[-1]  # Grab the newest of all
        return retval

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
