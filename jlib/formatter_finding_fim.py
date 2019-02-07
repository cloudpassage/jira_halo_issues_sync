from .base_formatter import BaseFormatter


class FormatterFindingFIM(BaseFormatter):
    """Format FIM finding json for Jira."""
    @classmethod
    def format(cls, finding_json):
        """Return a Jira-formatted representation of a FIM finding."""
        result = "h2. FIM failure: {}\n".format(finding_json["rule"]["target"])
        result += "Critical: {}\n".format(finding_json["rule"]["critical"])
        result += "{}\n".format(finding_json["rule"]["description"])
        result += "\n".join([cls.format_fim_finding(x)
                             for x in finding_json["findings"]])
        return result

    @classmethod
    def format_fim_finding(cls, fim_finding):
        retval = "* {}: {}".format(fim_finding["status"], fim_finding["file"])
        return retval
