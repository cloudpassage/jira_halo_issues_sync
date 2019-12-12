"""Manage configuration for application."""
import datetime
import os
import sys
import yaml
import dateutil.parser
from pathlib import Path

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
            reconciled between Halo and Jira.
        state_manager (None or instance of ManageState): This allows us to
            manage a timestamp placeholder between invocations.
        time_range (int): Number of minutes in the past to query for Halo
            issues to sync. Defaults to 15. This setting is ignored if AWS SSM
            is configured to manage the timestamp between invocations.
    """

    aws_ssm_default = "/CloudPassage-Jira/issues/timestamp"

    def __init__(self):
        self.logger = Logger()
        self.rules = self.set_rules()
        self.config = self.set_config()
        self.halo_api_key = os.getenv('HALO_API_KEY', "") or self.config.get('HALO_API_KEY')
        self.halo_api_secret_key = os.getenv('HALO_API_SECRET_KEY', "") or self.config.get('HALO_API_SECRET_KEY')
        self.halo_api_hostname = os.getenv('HALO_API_HOSTNAME', "") or self.config.get('HALO_API_HOSTNAME')
        self.jira_api_user = os.getenv('JIRA_API_USER', "") or self.config.get('JIRA_API_USER')
        self.jira_api_token = os.getenv('JIRA_API_TOKEN', "") or self.config.get('JIRA_API_TOKEN')
        self.jira_api_url = os.getenv('JIRA_API_URL', "") or self.config.get('JIRA_API_URL')
        self.time_range = int(os.getenv('TIME_RANGE', 15)) or self.config.get('TIME_RANGE')

        self.aws_ssm_timestamp_param = os.getenv("AWS_SSM_TIMESTAMP_PARAM",
                                                 self.aws_ssm_default)

        self.describe_issues_threads = int(os.getenv("DESCRIBE_ISSUES_THREADS", 10))
        self.determinator_threads = int(os.getenv("DETERMINATOR_THREADS", 5))
        self.reconciler_threads = int(os.getenv("RECONCILER_THREADS", 7))

        self.state_manager = None
        self.tstamp = self.set_timestamp_from_env() or self.set_timestamp_from_file()

    def required_vars_are_set(self):
        """Return True if all required vars are set, False otherwise."""
        required_vars_set = True
        missing_vars = []
        if not self.halo_api_key: missing_vars.append('HALO_API_KEY')
        if not self.halo_api_secret_key: missing_vars.append('HALO_API_SECRET_KEY')
        if not self.halo_api_hostname: missing_vars.append('HALO_API_HOSTNAME')
        if not self.jira_api_user: missing_vars.append('JIRA_API_USER')
        if not self.jira_api_token: missing_vars.append('JIRA_API_TOKEN')

        if missing_vars:
            msg = "Missing config attributes: {}".format(", ".join(missing_vars))
            self.logger.critical(msg)
            required_vars_set = False

        if not self.rules:
            self.logger.critical("At least one routing rule required in 'config/routing/'")
            required_vars_set = False

        for rule in self.rules:
            rule_missing = []
            try:
                if not rule['jira_config'].get('project_keys', None):
                    rule_missing.append('project_keys')
                if not rule['jira_config'].get('jira_issue_id_field', None):
                    rule_missing.append('jira_issue_id_field')
                if not rule['jira_config'].get('jira_issue_type', None):
                    rule_missing.append('jira_issue_type')
                if not rule['jira_config'].get('issue_close_transition', None):
                    rule_missing.append('issue_close_transition')
                if not rule['jira_config'].get('issue_reopen_transition', None):
                    rule_missing.append('issue_reopen_transition')
                if not rule['jira_config'].get('issue_status_closed', None):
                    rule_missing.append('issue_status_closed')
            except KeyError:
                self.logger.critical("Missing 'jira_config' field in rule yaml file")
                required_vars_set = False
            if rule_missing:
                msg = f"Missing 'jira_config' attributes in '{rule['name']}': {', '.join(rule_missing)}"
                self.logger.critical(msg)
                required_vars_set = False
        return required_vars_set

    def set_config(self):
        here_dir = os.path.abspath(os.path.dirname(__file__))
        config_dir = os.path.join(here_dir, '../config/etc')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        try:
            filename = os.fsdecode(os.listdir(config_dir)[0])
            filepath = os.path.join(config_dir, filename)
            with open(filepath, 'r') as stream:
                config = yaml.safe_load(stream)
                return config
        except IndexError:
            return {}
        except yaml.YAMLError as exc:
            self.logger.error(exc)

    def set_rules(self):
        rules = []
        here_dir = os.path.abspath(os.path.dirname(__file__))
        rules_dir = os.path.join(here_dir, '../config/routing')
        if not os.path.exists(rules_dir):
            os.makedirs(rules_dir)
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

    def set_timestamp_from_file(self):
        here_dir = os.path.abspath(os.path.dirname(__file__))
        tstamp_dir = os.path.join(here_dir, '../timestamp')
        try:
            tstamp_file = os.listdir(tstamp_dir)[0]
            tstamp = dateutil.parser.parse(os.fsdecode(tstamp_file))
        except (IndexError, ValueError):
            tstamp = (datetime.datetime.now()
                           - datetime.timedelta(minutes=(abs(self.time_range)))).isoformat()
        return tstamp

    def write_timestamp_to_file(self, timestamp):
        here_dir = os.path.abspath(os.path.dirname(__file__))
        tstamp_dir = os.path.join(here_dir, '../timestamp')
        if not os.path.exists(tstamp_dir):
            os.makedirs(tstamp_dir)
        new_file_path = os.path.join(tstamp_dir, timestamp)
        try:
            tstamp_filename = os.fsdecode(os.listdir(tstamp_dir)[0])
            old_file_path = os.path.join(tstamp_dir, tstamp_filename)
            os.rename(old_file_path, new_file_path)
        except IndexError:
            Path(new_file_path).touch()

    def set_timestamp_from_env(self):
        """Set self.tstamp for starting time.

        AWS-SSM configuration for supersedes the TIME_RANGE env var
        setting.
        """
        msg = "SSM timestamp param: {}".format(self.aws_ssm_timestamp_param)
        self.logger.info(msg)
        try:
            self.state_manager = ManageState(self.aws_ssm_timestamp_param)
            return self.state_manager.get_timestamp()
        except ValueError:
            return
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
