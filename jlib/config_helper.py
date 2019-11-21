"""Manage configuration for application."""
import datetime
import os
import sys
import yaml

from botocore.exceptions import ClientError
from botocore.exceptions import ParamValidationError

from .logger import Logger
from .manage_state import ManageState


class ConfigHelper(object):
    """Gather configuration from environment variables.

    Attributes:
        determinator_threads (int): Number of issues to be concurrently
            compared between Halo and Jira to determine the appropriate action
            to be taken (create, update, close, etc...).
        halo_api_key (str): Auditor API key for CloudPassage Halo.
        halo_api_secret_key (str): Halo API secret.
        halo_api_hostname (str): Halo API hostname.
        jira_api_token (str): API token for Jira.
        jira_api_url (str): URL for Jira API.
        reconciler_threads (int): Maximum number of issues to be simultameously
            recinciled between Halo and Jira.
        state_manager (None or instance of ManageState): This allows us to
            manage a timestamp placeholder between invocations.
        time_range (int): Number of minutes in the past to query for Halo
            issues to sync. Defaults to 15. This setting is ignored if AWS SSM
            is configured to manage the timestamp between invocations.
    """

    required_env = [
        "halo_api_key",
        "halo_api_secret_key",
        "jira_api_token",
        "jira_api_url",
        "jira_api_user",
        "time_range"
    ]

    aws_ssm_default = "/CloudPassage-Jira/issues/timestamp"

    def __init__(self):
        self.logger = Logger()
        self.rules = self.set_rules()
        self.halo_api_key = os.getenv('HALO_API_KEY', "")
        self.halo_api_secret_key = os.getenv('HALO_API_SECRET_KEY', "")
        self.halo_api_hostname = os.getenv('HALO_API_HOSTNAME', "")
        self.jira_api_user = os.getenv('JIRA_API_USER', "")
        self.jira_api_token = os.getenv('JIRA_API_TOKEN', "")
        self.jira_api_url = os.getenv('JIRA_API_URL', "")
        self.time_range = int(os.getenv('TIME_RANGE', 15))
        self.aws_ssm_timestamp_param = os.getenv("AWS_SSM_TIMESTAMP_PARAM",
                                                 self.aws_ssm_default)
        self.describe_issues_threads = int(os.getenv("DESCRIBE_ISSUES_THREADS", 10))
        self.determinator_threads = int(os.getenv("DETERMINATOR_THREADS", 5))
        self.reconciler_threads = int(os.getenv("RECONCILER_THREADS", 7))

        self.state_manager = None
        self.set_timestamp_from_env()

    def required_vars_are_set(self):
        """Return True if all required vars are set, False otherwise."""
        required_vars_set = True
        env_missing = [x for x in self.required_env
                   if getattr(self, x) in [0, ""]
                   and not isinstance(getattr(self, x), bool)]
        if env_missing:
            msg = "Missing config attributes: {}".format(", ".join(env_missing))
            self.logger.critical(msg)
            required_vars_set = False

        for rule in self.rules:
            config_missing = []
            if not rule['jira_config']['project_keys']: config_missing.append('project_keys')
            if not rule['jira_config']['jira_issue_id_field']: config_missing.append('jira_issue_id_field')
            if not rule['jira_config']['jira_issue_type']: config_missing.append('jira_issue_type')
            if not rule['jira_config']['issue_close_transition']: config_missing.append('issue_close_transition')
            if not rule['jira_config']['issue_reopen_transition']: config_missing.append('issue_reopen_transition')
            if not rule['jira_config']['issue_status_closed']: config_missing.append('issue_status_closed')
            if config_missing:
                msg = f"Missing config attributes in {rule['name']}: {', '.join(config_missing)}"
                self.logger.critical(msg)
                required_vars_set = False
        return required_vars_set

    def set_rules(self):
        rules = []
        here_dir = os.path.abspath(os.path.dirname(__file__))
        rules_dir = os.path.join(here_dir, '../config/routing')
        for file in os.listdir(rules_dir):
            filename = os.fsdecode(file)
            filepath = os.path.join(rules_dir, filename)
            with open(filepath, 'r') as stream:
                try:
                    rule = yaml.safe_load(stream)
                    rule["name"] = filename
                    rules.append(rule)
                except yaml.YAMLError as exc:
                    self.logger.error(exc)
        return rules

    def set_timestamp_from_env(self):
        """Set self.tstamp for starting time.

        AWS-SSM configuration for supersedes the TIME_RANGE env var
        setting.
        """
        msg = "SSM timestamp param: {}".format(self.aws_ssm_timestamp_param)
        self.logger.info(msg)
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
        except ParamValidationError as e:
            self.logger.error("SSM Parameter validation failed: {}".format(e))
            sys.exit(1)
