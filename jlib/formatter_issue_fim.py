from .base_formatter import BaseFormatter


class FormatterIssueFIM(BaseFormatter):
    """Format FIM issue json for Jira."""
    @classmethod
    def format_header(cls, issue_json):
        return "h2. FIM issue: {}\n".format(issue_json["name"])
