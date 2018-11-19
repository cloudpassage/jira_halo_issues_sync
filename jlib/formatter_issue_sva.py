from base_formatter import BaseFormatter


class FormatterIssueSVA(BaseFormatter):
    """Format SVA issue json for Jira."""
    @classmethod
    def format_header(cls, issue_json):
        return "h2. Vulnerable software package: {}\n".format(issue_json["name"])  # NOQA
