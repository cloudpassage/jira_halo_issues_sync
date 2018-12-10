from base_formatter import BaseFormatter


class FormatterIssueSVA(BaseFormatter):
    """Format SVA issue json for Jira."""
    @classmethod
    def format_header(cls, issue_json):
        pkg_name = issue_json["name"]
        hdr = "h2. Vulnerable software package: {}\n".format(pkg_name)
        return hdr
