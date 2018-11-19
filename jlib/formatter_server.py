from base_formatter import BaseFormatter


class FormatterServer(BaseFormatter):
    """Format server json for Jira."""
    @classmethod
    def format(cls, asset_json):
        """Return a Jira-formatted representation of a server."""
        result = "h2. Server {} at {}\n".format(asset_json["hostname"],
                                                asset_json["reported_fqdn"])
        fields = sorted([cls.format_field(asset_json, field_name)
                         for field_name in asset_json.keys()])
        result += "\n".join([field for field in fields if field != ""])
        return result
