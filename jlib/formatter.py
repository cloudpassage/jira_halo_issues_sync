"""Entrypoint for formatting assets, issues, and findings."""
import json


class Formatter(object):

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
        summary = f'Source: {issue_described["source"]} ' \
                  f'Issue - Critical: {issue_described["critical"]} - ' \
                  f'Type: {issue_described["type"]} - ' \
                  f'Name: {issue_described["name"]}'
        return summary
