"""Manage configuration for application."""
import datetime
import os
import sys

from botocore.exceptions import ClientError

from .logger import Logger
from .manage_state import ManageState


class ConfigHelper(object):
    """Gather configuration from environment variables.

    Attributes:
        critical_only (bool): Only sync critical issues.
        determinator_threads (int): Number of issues to be concurrently
            compared between Halo and Jira to determine the appropriate action
            to be taken (create, update, close, etc...).
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
        reconciler_threads (int): Maximum number of issues to be simultameously
            recinciled between Halo and Jira.
        state_manager (None or instance of ManageState): This allows us to
            manage a timestamp placeholder between invocations.
        time_range (int): Number of minutes in the past to query for Halo
            issues to sync. Defaults to 15. This setting is ignored if AWS SSM
            is configured to manage the timestamp between invocations.
    """

    concurrency_defaults = {"describe_issues_threads": 10,
                            "determinator_threads": 5,
                            "reconciler_threads": 7}

    required = ["critical_only",
                "determinator_threads",
                "halo_api_key",
                "halo_api_secret_key",
                "issue_close_transition",
                "issue_reopen_transition",
                "issue_status_closed",
                "jira_api_token",
                "jira_api_url",
                "jira_api_user",
                "jira_issue_id_field",
                "jira_issue_type",
                "jira_project_key",
                "reconciler_threads",
                "time_range"]

    def __init__(self):
        self.ref = [("critical_only", self.bool_from_env),
                    ("halo_api_key", self.str_from_env),
                    ("halo_api_secret_key", self.str_from_env),
                    ("halo_api_hostname", self.str_from_env),
                    ("jira_api_user", self.str_from_env),
                    ("jira_api_token", self.str_from_env),
                    ("jira_api_url", self.str_from_env),
                    ("jira_field_static", self.dict_from_env),
                    ("jira_field_mapping", self.dict_from_env),
                    ("jira_issue_id_field", self.str_from_env),
                    ("jira_project_key", self.str_from_env),
                    ("jira_issue_type", self.str_from_env),
                    ("issue_close_transition", self.str_from_env),
                    ("issue_status_closed", self.str_from_env),
                    ("issue_status_hard_closed", self.str_from_env),
                    ("issue_reopen_transition", self.str_from_env),
                    ("aws_ssm_timestamp_param", self.str_from_env),
                    ("time_range", self.int_from_env)]
        self.logger = Logger()
        self.aws_ssm_timestamp_param = "/CloudPassage-Jira/issues/timestamp"
        self.set_config_from_env()
        self.state_manager = None
        self.set_timestamp_from_env()

    @classmethod
    def bool_from_env(cls, var_name):
        """Return True if env var is set to "True" or "true", else False."""
        logger = Logger()
        result = False
        if os.getenv(var_name) in ["True", "true"]:
            result = True
        logger.info("Setting {} to {}".format(var_name, str(result)))
        return result

    @classmethod
    def dict_from_env(cls, var_name):
        """Return dict derived from env var.

        K:V;K:V
        """
        logger = Logger()
        try:
            result = {x.split(":")[0]: x.split(":")[1]
                      for x in os.getenv(var_name).split(";")}
        except AttributeError:
            result = {}
        except IndexError:
            result = {}
        logger.info("Setting {} to {}".format(var_name, str(result)))
        return result

    @classmethod
    def int_from_env(cls, var_name):
        """Return integer derived from env var."""
        logger = Logger()
        result = int(os.getenv(var_name, 0))
        logger.info("Setting {} to {}".format(var_name, str(result)))
        return result

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
        missing = [x for x in self.required
                   if getattr(self, x) in [0, ""]
                   and not isinstance(getattr(self, x), bool)]
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
            env_var_name = varname.upper()
            result = env_getter(env_var_name)
            setattr(self, varname, result)
        # Set concurrency vars
        for varname, default in self.concurrency_defaults.items():
            setattr(self, varname, int(os.getenv(varname.upper(), default)))

    def set_timestamp_from_env(self):
        """Set self.tstamp for starting time.

        AWS-SSM configuration for supersedes the TIME_RANGE env var
        setting.
        """
        try:
            self.state_manager = ManageState(self.aws_ssm_timestamp_param)
            self.tstamp = self.state_manager.get_timestamp()
        except ValueError:
            self.tstamp = (datetime.datetime.now()
                           - datetime.timedelta(minutes=(abs(self.time_range)))).isoformat()  # NOQA
        except ClientError as e:
            if "ParameterNotFound" in repr(e):
                msg = ("Parameter {} not found. Will create param, set it and "
                       "exit.".format(self.aws_ssm_timestamp_param))
                tstamp = (datetime.datetime.now()
                          - datetime.timedelta(minutes=(abs(self.time_range)))).isoformat()  # NOQA
                self.state_manager.set_timestamp(tstamp)
                self.logger.error(msg)
                sys.exit(1)
            msg = "AWS role configuration issue: {}".format(e)
            self.logger.error(msg)
            sys.exit(1)
