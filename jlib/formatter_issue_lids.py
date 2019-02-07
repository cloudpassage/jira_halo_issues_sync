from .base_formatter import BaseFormatter


class FormatterIssueLIDS(BaseFormatter):
    """Format LIDS issue json for Jira."""
    @classmethod
    def format_header(cls, issue_json):
        return "h2. Log-based IDS issue: {}\n".format(issue_json["name"])
