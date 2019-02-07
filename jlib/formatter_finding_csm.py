from .base_formatter import BaseFormatter


class FormatterFindingCSM(BaseFormatter):
    """Format CSM finding json for Jira."""
    @classmethod
    def format(cls, finding_json):
        """Return a Jira-formatted representation of a CSM finding."""
        result = "h2. Config failure: {}\n".format(finding_json["rule_name"])
        result += "Critical: {}\n".format(finding_json["critical"])
        result += "{}\n".format(finding_json["rule_description"])
        return result
