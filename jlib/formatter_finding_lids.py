from base_formatter import BaseFormatter


class FormatterFindingLIDS(BaseFormatter):
    """Format LIDS event json for Jira."""
    @classmethod
    def format(cls, event_json):
        """Return a Jira-formatted representation of a LIDS event."""
        result = "h2. {}\n".format(event_json["name"])
        result += "Critical: {}\n".format(event_json["critical"])
        result += "{}\n".format(event_json["rule_name"])
        result += "{}\n".format(event_json["message"])
        return result
