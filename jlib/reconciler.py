"""Reconcile Halo issues against Jira."""
from multiprocessing.dummy import Pool as ThreadPool

from .formatter import Formatter
from .halo import Halo
from .jira_local import JiraLocal
from .logger import Logger
from .mapper import Mapper


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
    supported_actions = ["create", "create_closed", "comment", "change_status"]

    def __init__(self, halo, jira, dynamic_mapping, static_mapping):
        self.logger = Logger()
        self.halo = halo
        self.jira = jira
        self.dynamic_mapping = dynamic_mapping
        self.static_mapping = static_mapping
        return

    @classmethod
    def reconcile_marching_orders(cls, config, orders_dict):
        batch_size = config.reconciler_threads * 2
        halo = Halo(config.halo_api_key, config.halo_api_secret_key,
                    config.halo_api_hostname, config.describe_issues_threads)
        jira = JiraLocal(config.jira_api_url, config.jira_api_user,
                         config.jira_api_token,
                         config.jira_issue_id_field,
                         config.jira_project_key,
                         config.jira_issue_type)
        marching_orders = list(orders_dict.items())
        ordered_actions = sorted(marching_orders, key=cls.get_tstamp)
        packed_list = [{"config": config,
                        "issue_id": x[0],
                        "halo": halo,
                        "jira": jira,
                        "other": x[1]}.copy()
                       for x in ordered_actions]
        reconciler_helper = cls.reconcile_issue
        while packed_list:
            this_batch = packed_list[:batch_size]
            del packed_list[:batch_size]
            last_in_batch = this_batch[-1].copy()
            batch_timestamp = cls.get_tstamp_from_packed(last_in_batch)
            pool = ThreadPool(config.reconciler_threads)
            pool.map(reconciler_helper, this_batch)
            pool.close()
            pool.join()
            if config.state_manager:
                config.state_manager.increment_timestamp(batch_timestamp)
        if config.state_manager:
            config.state_manager.set_timestamp(batch_timestamp)
        return

    @classmethod
    def get_tstamp(cls, order):
        """Return the tstamp from the 'halo' section of a marching order."""
        return order[1]["halo"]["tstamp"]

    @classmethod
    def get_tstamp_from_packed(cls, packed):
        """Return the tstamp from the 'halo' section of a packed action."""
        return packed["other"]["halo"]["tstamp"]

    @classmethod
    def reconcile_issue(cls, reconcile_bundle):
        """Reconcile Halo issue lifecycle state with Jira.

        Args:
            reconcile_bundle (dict): Dictionary with the following keys:
                ``config``, ``issue_id``, ``halo``, ``jira``, ``other``.

        """
        config = reconcile_bundle["config"]
        issue_id = reconcile_bundle["issue_id"]
        halo = reconcile_bundle["halo"]
        jira = reconcile_bundle["jira"]
        other = reconcile_bundle["other"]
        logger = Logger()
        reconciler = cls(halo, jira, config.jira_field_mapping,
                         config.jira_field_static)
        action = other["disposition"][0]
        if action == "create":
            msg = "Creating Jira issue for Halo issue ID {}".format(issue_id)
        elif action == "create_closed":
            msg = ("Creating and closing Jira issue for Halo issue "
                   "ID {}".format(issue_id))
        elif action == "comment":
            if config.no_comment:
                msg = ("Commenting suppressed in config, skipping Halo issue "
                       "{}".format(issue_id))
                logger.info(msg)
                return
            msg = "Commenting Jira issue for Halo issue ID {}".format(issue_id)
        elif action == "change_status":
            msg = ("Transitioning Jira issue for Halo issue ID "
                   "{}".format(issue_id))
        elif action == "nothing":
            logger.info("Nothing to do for Halo issue ID {}".format(issue_id))
        logger.info(msg)
        reconciler.reconcile(other["disposition"], other["halo"])

    def reconcile(self, determination, issue_meta):
        """Return tuple (True, ) for success, else (False, "reason")."""
        action, instructions = determination
        issue_id = issue_meta["id"]
        module = issue_meta["issue_type"]
        message = "Halo ID: {}\tModule: {}\tAction: {}".format(issue_id,
                                                               module, action)
        self.logger.info(message)
        self.logger.debug("Halo ID: {}\tModule: {}\tAction: {}\t"
                          "Instructions: {}".format(issue_id, module, action,
                                                    instructions))
        if action not in self.supported_actions:
            msg = "Unsupported action for {}: {}".format(issue_meta["id"],
                                                         action)
            self.logger.warn(msg)
            return
        elif action == "create":
            self.create(issue_meta)
        elif action == "create_closed":
            self.create_closed(issue_meta, instructions["transition"])
        elif action == "comment":
            self.comment(issue_meta, instructions["jira_id"])
        elif action == "change_status":
            self.change_status(instructions["jira_id"],
                               instructions["transition"])
        return

    def create(self, issue_described):
        """Create an issue in Jira for corresponding Halo issue."""
        issue_type = issue_described["issue_type"]
        # This will be refactored when we support more asset types.
        asset_type = "server" if "agent_id" in issue_described else "Unrecognized"  # NOQA
        asset_id = issue_described["agent_id"] if asset_type == "server" else "NONE"  # NOQA
        asset_described = self.halo.describe_asset(asset_type, asset_id)
        asset_formatted = Formatter.format_object("asset", "server",
                                                  asset_described)

        issue_type = issue_described["issue_type"]
        issue_formatted = Formatter.format_object("issue", issue_type,
                                                  issue_described)

        finding_meta = issue_described["findings"][-1]
        finding_described = self.halo.describe_finding(finding_meta["finding"])
        finding_formatted = Formatter.format_object("finding", issue_type,
                                                    finding_described)
        summary = Formatter.format_summary(asset_type, issue_type,
                                           asset_described, issue_described)
        description = "\n----\n".join([finding_formatted, asset_formatted,
                                       issue_formatted])
        halo_issue_id = issue_described["id"]
        field_mapping = Mapper.map_fields(self.dynamic_mapping,
                                          self.static_mapping,
                                          asset_described,
                                          issue_described)
        result = self.jira.create_jira_issue(summary, description,
                                             halo_issue_id, field_mapping)
        return result

    def create_closed(self, issue_described, transition):
        jira_issue = self.create(issue_described)
        self.change_status(jira_issue, transition)
        return

    def comment(self, issue_described, jira_issue_id):
        try:
            issue_type = issue_described["issue_type"]
            finding_meta = issue_described["findings"][-1]
        except KeyError as e:
            msg = ("Unable to parse Halo issue: "
                   "{}\n{}".format(str(e), str(issue_described)))
            self.logger.error(msg)
        finding_described = self.halo.describe_finding(finding_meta["finding"])
        finding_formatted = Formatter.format_object("finding", issue_type,
                                                    finding_described)
        self.jira.comment_jira_issue(jira_issue_id, finding_formatted)

        return

    def change_status(self, issue_id, transition):
        self.jira.jira_issue_transition(issue_id, transition)
        return
