from .base_formatter import BaseFormatter


class FormatterIssueCSM(BaseFormatter):
    @classmethod
    def format_header(cls, issue_json):
        return "h2. Configuration issue: {}\n".format(issue_json["name"])
