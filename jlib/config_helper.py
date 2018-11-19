"""Manage configuration for application."""
import datetime
import os
from logger import Logger


class ConfigHelper(object):
    """Gather configuration from environment variables.

    Attributes:
        critical_only (bool): Only sync critical issues.
        halo_api_key (str): Auditor API key for CloudPassage Halo.
        halo_api_secret_key (str): Halo API secret.
        halo_api_hostname (str): Halo API hostname.
        jira_api_token (str): API token for Jira.
        jira_api_url (str): URL for Jira API.
        jira_field_static (dict): Fields to statically populate in Jira.
        jira_field_mapping (dict): Fields to map from Halo to Jira.
        jira_issue_id_field (str): Halo issue ID will be stored in this field,
            in Jira.
        jira_project_key (str): Key for Jira project where all issues will be
            created.
        jira_issue_type (str): Type of issue to open (bug, etc...)
        issue_close_transition (str): This transition will be used for closing
            Jira issues.
        issue_status_hard_closed (str): Issues with this status will not be
            reopened. Instead, a new Jira issue will be created.
        issue_reopen_transition (str): Reopened issues will be ceated with this
            status.
        time_range (int): Number of minutes in the past to query for Halo
            issues to sync.
    """

    required = ["critical_only",
                "halo_api_key",
                "halo_api_secret_key",
                "jira_api_user",
                "jira_api_token",
                "jira_api_url",
                "jira_issue_id_field",
                "jira_project_key",
                "jira_issue_type",
                "issue_status_closed",
                "issue_close_transition",
                "issue_reopen_transition",
                "time_range"]

    def __init__(self):
        self.ref = [("critical_only", self.bool_from_env, "CRITICAL_ONLY"),
                    ("halo_api_key", self.str_from_env, "HALO_API_KEY"),
                    ("halo_api_secret_key", self.str_from_env, "HALO_API_SECRET_KEY"),  # NOQA
                    ("halo_api_hostname", self.str_from_env, "HALO_API_HOSTNAME"),  # NOQA
                    ("jira_api_user", self.str_from_env, "JIRA_API_USER"),
                    ("jira_api_token", self.str_from_env, "JIRA_API_TOKEN"),
                    ("jira_api_url", self.str_from_env, "JIRA_API_URL"),
                    ("jira_field_static", self.dict_from_env, "JIRA_FIELD_STATIC"),  # NOQA
                    ("jira_field_mapping", self.dict_from_env, "JIRA_FIELD_MAPPING"),  # NOQA
                    ("jira_issue_id_field", self.str_from_env, "JIRA_ISSUE_ID_FIELD"),  # NOQA
                    ("jira_project_key", self.str_from_env, "JIRA_PROJECT_KEY"),  # NOQA
                    ("jira_issue_type", self.str_from_env, "JIRA_ISSUE_TYPE"),
                    ("issue_close_transition", self.str_from_env, "ISSUE_CLOSE_TRANSITION"),  # NOQA
                    ("issue_status_closed", self.str_from_env, "ISSUE_STATUS_CLOSED"),  # NOQA
                    ("issue_status_hard_closed", self.str_from_env, "ISSUE_STATUS_HARD_CLOSED"),  # NOQA
                    ("issue_reopen_transition", self.str_from_env, "ISSUE_REOPEN_TRANSITION"),  # NOQA
                    ("time_range", self.int_from_env, "TIME_RANGE")]
        self.set_config_from_env()
        self.tstamp = (datetime.datetime.now()
                       - datetime.timedelta(minutes=(abs(5000)))).isoformat()
        self.logger = Logger()


    @classmethod
    def bool_from_env(cls, var_name):
        """Return True if env var is set to "True" or "true", else False."""
        if os.getenv(var_name) in ["True", "true"]:
            return True
        elif os.getenv(var_name) in ["False", "false"]:
            return False
        return False

    @classmethod
    def dict_from_env(cls, var_name):
        """Return dict derived from env var.

        K:V;K:V
        """
        try:
            result = {x.split(":")[0]: x.split(":")[1]
                      for x in os.getenv(var_name).split(";")}
        except AttributeError:
            result = {}
        except IndexError:
            result = {}
        return result


    @classmethod
    def int_from_env(cls, var_name):
        """Return integer derived from env var."""
        return int(os.getenv(var_name, 0))

    @classmethod
    def list_from_env(cls, var_name):
        """Return a list derived from comma-separated value of env var."""
        try:
            return os.getenv(var_name).split(",")
        except AttributeError:
            return []

    @classmethod
    def str_from_env(cls, var_name):
        """Return string from env var."""
        return os.getenv(var_name, "")

    def required_vars_are_set(self):
        """Return True if all required vars are set, False otherwise."""
        missing = [x for x in self.required if getattr(self, x) in [0, ""]]
        if missing:
            msg = "Missing config attributes: {}".format(", ".join(missing))
            self.logger.critical(msg)
            return False
        return True

    def set_config_from_env(self):
        """Set instance attributes from env vars."""
        for setting in self.ref:
            varname = setting[0]
            env_getter = setting[1]
            env_var_name = setting[2]
            result = env_getter(env_var_name)
            setattr(self, varname, result)
