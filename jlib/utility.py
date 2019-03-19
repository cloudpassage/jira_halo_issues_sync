"""Utility functions which don't need dedicated classes live here."""
from multiprocessing.dummy import Pool as ThreadPool

from .determinator import Determinator
from .jira_local import JiraLocal
from .logger import Logger


class Utility(object):
    @classmethod
    def print_initial_job_stats(cls, tstamp, issues):
        """Log initial job stats."""
        logger = Logger()
        msgs = []
        if issues == []:
            return
        msgs.append("Reconciling {} Halo issues since {}".format(len(issues),
                                                                 tstamp))
        c_time = sorted([x["created_at"] for x in issues])
        msgs.append("Create times between: {} and {}".format(c_time[0],
                                                             c_time[-1]))
        ls_time = sorted([x["last_seen_at"] for x in issues])
        msgs.append("Last seen times between: {} and {}".format(ls_time[0],
                                                                ls_time[-1]))
        r_time = sorted([x["resolved_at"] for x in issues])
        msgs.append("Resolved times between: {} and {}".format(r_time[0],
                                                               r_time[-1]))
        for issue_type in ["lids", "csm", "fim", "sva", "sam", "fw", "agent"]:
            count_this_type = [x for x in issues
                               if x["issue_type"] == issue_type]
            msgs.append("Issue type {}: {}".format(issue_type,
                                                   len(count_this_type)))
        for msg in msgs:
            logger.info(msg)
        return

    @classmethod
    def get_marching_orders(cls, config, issue_list):
            """Map Halo issue IDs to thread pool for checking Jira issues."""
            packed_list = [(config, x) for x in issue_list]
            determinator = Determinator(config.issue_status_closed,
                                        config.issue_close_transition,
                                        config.issue_status_hard_closed,
                                        config.issue_reopen_transition)
            issue_correlator_helper = cls.jira_issue_correlator
            pool = ThreadPool(config.determinator_threads)
            correlated_issues = pool.map(issue_correlator_helper, packed_list)
            pool.close()
            pool.join()
            # Key is Halo issue ID, value is dict containing keys for
            # disposition, Halo issue, and Jira issue.
            marching_orders = {x["halo"]["id"]: {"disposition": determinator.get_disposition(x["halo"], x["jira"]),  # NOQA
                                                 "halo": x["halo"],
                                                 "jira": x["jira"]}
                               for x in correlated_issues}
            return marching_orders

    @classmethod
    def jira_issue_correlator(cls, get_tup):
        """Gets Jira issues related to a Halo issue ID.
        Args:
            get_tup(tuple): First item in tuple is the config object.  The
                second is the Halo issue object of interest.
        Returns:
            dict: Halo issue information
        """
        config, halo_issue = get_tup
        jira = JiraLocal(config.jira_api_url, config.jira_api_user,
                         config.jira_api_token,
                         config.jira_issue_id_field,
                         config.jira_project_key,
                         config.jira_issue_type)
        jira_related = jira.get_jira_issues_for_halo_issue(halo_issue["id"])
        return {"halo": halo_issue, "jira": jira_related}
