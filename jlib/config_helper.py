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
        halo_api_key (str): Auditor API key for CloudPassage Halo.
        halo_api_secret_key (str): Halo API secret.
        halo_api_hostname (str): Halo API hostname.
        jira_api_token (str): API token for Jira.
        jira_api_url (str): URL for Jira API.
        state_manager (None or instance of ManageState): This allows us to
            manage a timestamp placeholder between invocations.
        time_range (int): Number of minutes in the past to query for Halo
            issues to sync. Defaults to 15. This setting is ignored if AWS SSM
            is configured to manage the timestamp between invocations.
    """

    def __init__(self):
        self.logger = Logger()
        self.rules = self.set_rules()
        self.config = self.set_config()
        self.halo_api_key = os.getenv('HALO_API_KEY') or self.config.get('HALO_API_KEY')
        self.halo_api_secret_key = os.getenv('HALO_API_SECRET_KEY') or self.config.get('HALO_API_SECRET_KEY')
        self.halo_api_hostname = os.getenv('HALO_API_HOSTNAME') or self.config.get('HALO_API_HOSTNAME')
        self.jira_api_user = os.getenv('JIRA_API_USER') or self.config.get('JIRA_API_USER')
        self.jira_api_token = os.getenv('JIRA_API_TOKEN') or self.config.get('JIRA_API_TOKEN')
        self.jira_api_url = os.getenv('JIRA_API_URL') or self.config.get('JIRA_API_URL')
        self.time_range = int(os.getenv('TIME_RANGE', 15)) or self.config.get('TIME_RANGE')
        self.aws_ssm_timestamp_param = os.getenv("AWS_SSM_TIMESTAMP_PARAM", "/CloudPassage-Jira/issues/timestamp")
        self.state_manager = None
        self.tstamp = self.set_timestamp_from_env() or self.set_timestamp_from_file()

    def required_vars_are_set(self):
        """Return True if all required vars are set, False otherwise."""
        required_vars_set = True
        missing_vars = []
        if not self.halo_api_key:
            missing_vars.append('HALO_API_KEY')
        if not self.halo_api_secret_key:
            missing_vars.append('HALO_API_SECRET_KEY')
        if not self.halo_api_hostname:
            missing_vars.append('HALO_API_HOSTNAME')
        if not self.jira_api_user:
            missing_vars.append('JIRA_API_USER')
        if not self.jira_api_token:
            missing_vars.append('JIRA_API_TOKEN')

        if missing_vars:
            self.logger.critical(f"Missing config attributes: {','.join(missing_vars)}")
            required_vars_set = False

        if not self.rules:
            self.logger.critical("At least one routing rule .yaml file required in 'config/routing/'")
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
                self.logger.critical(f"Missing 'jira_config' field in {rule['name']}")
                required_vars_set = False
            if rule_missing:
                msg = f"Missing 'jira_config' attributes in '{rule['name']}': {', '.join(rule_missing)}"
                self.logger.critical(msg)
                required_vars_set = False
        return required_vars_set

    def set_config(self):
        config = {}
        config_dir = self.relpath_to_abspath('../config/etc')
        if not os.path.exists(config_dir):
            return config
        try:
            file_path = list(os.scandir(config_dir))[0].path
            return self.open_yaml(file_path)
        except IndexError:
            return config

    def set_rules(self):
        rules = []
        rules_dir = self.relpath_to_abspath('../config/routing')
        if not os.path.exists(rules_dir):
            return rules
        for file in os.scandir(rules_dir):
            rule = self.open_yaml(file.path)
            rule['name'] = file.path.split('/')[-1]
            rules.append(rule)
        return rules

    def open_yaml(self, path):
        with open(path, 'r') as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                self.logger.error(exc)

    @staticmethod
    def relpath_to_abspath(rel_path):
        here_dir = os.path.abspath(os.path.dirname(__file__))
        abs_path = os.path.join(here_dir, rel_path)
        return abs_path

    def set_timestamp_from_file(self):
        tstamp_dir = self.relpath_to_abspath('../timestamp')
        try:
            tstamp_file = os.listdir(tstamp_dir)[0]
            tstamp = dateutil.parser.parse(os.fsdecode(tstamp_file))
        except (IndexError, ValueError):
            tstamp = (datetime.datetime.now()
                           - datetime.timedelta(minutes=(abs(self.time_range)))).isoformat()
        return tstamp

    def write_timestamp_to_file(self, timestamp):
        tstamp_dir = self.relpath_to_abspath('../timestamp')
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
