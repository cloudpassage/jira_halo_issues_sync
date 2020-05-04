"""Entrypoint for formatting assets, issues, and findings."""
import json


class Formatter(object):

    # core_issue_fields = ['name', 'type', 'status', 'critical', 'source', 'first_seen_at', 'last_seen_at',
    #                      'policy_name', 'cp_rule_id', 'rule_name', 'resolved_at', 'resolved_by', 'resolution_comment'
    #                      'time_to_resolution', 'package_name', 'package_version', 'cve_ids', 'max_cvss',
    #                      'remotely_exploitable', ]
    #
    # core_asset_fields = ['asset_name', 'asset_type', 'group_name', 'csp_account_id', 'csp_account_type',
    #                      'csp_account_name', 'csp_region', 'csp_service_type', 'csp_resource_id', 'csp_tags',
    #                      'csp_image_id', 'csp_resource_uri', 'os_type', 'registry_name', ]

    @classmethod
    def format_object(cls, object_type, object_json):
        """Return Jira-formatted text describing object.

        Args:
            object_type (str): Must match cls.supported_object_types
            object_json (str): Halo object json to be formatted.

        Returns:
            str: Jira-formatted text describing object.
        """
        formatted = f'h2. {object_type}\n' + '{code:JSON}' + json.dumps(object_json, indent=2) + '{code}\n\n'
        return formatted

    @classmethod
    def format_summary(cls, issue_described):
        """Format summary string."""
        summary = issue_described["name"]
        return summary
