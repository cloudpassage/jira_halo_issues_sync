from .base_formatter import BaseFormatter


class FormatterFindingSVA(BaseFormatter):
    """Format LIDS event json for Jira."""
    @classmethod
    def format(cls, finding):
        """Return a Jira-formatted representation of a SVA event."""
        result = "h2. Vulnerable package: {} version {}\n".format(finding["package_name"], finding["package_version"])  # NOQA
        result += "Critical: {}\n".format(finding["critical"])
        result += "\n".join([cls.format_cve_entry(x)
                             for x in finding["cve_entries"]])
        return result

    @classmethod
    def format_cve_entry(cls, entry):
        """Return CVE entry formatted for Jira."""
        return "{} Score: {} Supressed: {}".format(entry["cve_entry"],
                                                   entry["cvss_score"],
                                                   entry["suppressed"])
