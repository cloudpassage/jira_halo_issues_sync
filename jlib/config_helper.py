"""Manage configuration for application."""
import os
import yaml
from jira import JIRA
from jira.exceptions import JIRAError
from .logger import Logger


class ConfigHelper(object):
    """Gather configuration from environment variables.

    Attributes:
        halo_api_key (str): Auditor API key for CloudPassage Halo.
        halo_api_secret_key (str): Halo API secret.
        halo_api_hostname (str): Halo API hostname.
        jira_api_token (str): API token for Jira.
        jira_api_url (str): URL for Jira API.
    """

    def __init__(self):
        self.logger = Logger()
        self.rules = self.set_rules()
        # pprint(self.rules)
        self.config = self.set_config()
        self.halo_api_key = os.getenv('HALO_API_KEY') or self.config.get('HALO_API_KEY')
        self.halo_api_secret_key = os.getenv('HALO_API_SECRET_KEY') or self.config.get('HALO_API_SECRET_KEY')
        self.halo_api_hostname = os.getenv('HALO_API_HOSTNAME') or \
                                 self.config.get('HALO_API_HOSTNAME', "api.cloudpassage.com")
        self.jira_api_user = os.getenv('JIRA_API_USER') or self.config.get('JIRA_API_USER')
        self.jira_api_token = os.getenv('JIRA_API_TOKEN') or self.config.get('JIRA_API_TOKEN')
        self.jira_api_url = os.getenv('JIRA_API_URL') or self.config.get('JIRA_API_URL')
        self.jira_fields_dict = self.set_jira_fields(self.jira_api_user, self.jira_api_token, self.jira_api_url)

    def set_jira_fields(self, auth_user, auth_token, jira_url):
        jira = JIRA(jira_url, basic_auth=(auth_user, auth_token))
        jira_fields = {}
        for field in jira.fields():
            jira_fields[field["name"]] = field["id"]
            jira_fields[field["id"]] = field["id"]
        return jira_fields

    def validate_config(self):
        """Return True if all required vars are set, False otherwise."""
        validation_passed = True
        validation_passed = self.validate_creds()
        validation_passed = self.validate_rules()
        validation_passed = self.validate_jira_fields()
        return validation_passed

    def validate_jira_fields(self):
        validation_passed = True
        if self.rules:
            for rule in self.rules:
                invalid_fields = []
                fields = rule.get("fields") or {}
                mapping = fields.get("mapping") or {}
                static = fields.get("static") or {}
                for value in mapping.values():
                    if value not in self.jira_fields_dict:
                        invalid_fields.append(value)
                for key in static.keys():
                    if key not in self.jira_fields_dict:
                        invalid_fields.append(key)
                if invalid_fields:
                    self.logger.critical(f"Invalid field names in '{rule['name']}': {', '.join(invalid_fields)}")
                    validation_passed = False
        return validation_passed

    def validate_creds(self):
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
            return False
        return True

    def validate_rules(self):
        validation_passed = True
        if not self.rules:
            self.logger.critical("At least one routing rule .yaml file required in 'config/routing/'")
            return False

        for rule in self.rules:
            rule_missing = []
            try:
                if not rule['jira_config'].get('project_keys', None):
                    rule_missing.append('project_keys')
                if not rule['jira_config'].get('jira_issue_id_field', None):
                    rule_missing.append('jira_issue_id_field')
                if not rule['jira_config'].get('jira_issue_type', None):
                    rule_missing.append('jira_issue_type')
                if not rule['jira_config'].get('issue_status_active', None):
                    rule_missing.append('issue_status_active')
                if not rule['jira_config'].get('issue_status_closed', None):
                    rule_missing.append('issue_status_closed')
                if not rule['jira_config'].get('issue_status_reopened', None):
                    rule_missing.append('issue_status_reopened')
            except KeyError:
                self.logger.critical(f"Missing 'jira_config' field in {rule['name']}")
                validation_passed = False
                continue
            if rule_missing:
                msg = f"Missing 'jira_config' attributes in '{rule['name']}': {', '.join(rule_missing)}"
                self.logger.critical(msg)
                validation_passed = False
        return validation_passed

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
