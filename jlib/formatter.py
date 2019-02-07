"""Entrypoint for formatting assets, issues, and findings."""
from .logger import Logger
from .formatter_finding_csm import FormatterFindingCSM
from .formatter_finding_fim import FormatterFindingFIM
from .formatter_finding_lids import FormatterFindingLIDS
from .formatter_finding_sva import FormatterFindingSVA
from .formatter_issue_csm import FormatterIssueCSM
from .formatter_issue_fim import FormatterIssueFIM
from .formatter_issue_lids import FormatterIssueLIDS
from .formatter_issue_sva import FormatterIssueSVA
from .formatter_server import FormatterServer


class Formatter(object):
    supported_asset_types = {"server": FormatterServer}
    supported_finding_types = {"csm": FormatterFindingCSM,
                               "fim": FormatterFindingFIM,
                               "lids": FormatterFindingLIDS,
                               "sva": FormatterFindingSVA}
    supported_issue_types = {"csm": FormatterIssueCSM,
                             "fim": FormatterIssueFIM,
                             "lids": FormatterIssueLIDS,
                             "sva": FormatterIssueSVA}
    supported_object_types = {"asset": supported_asset_types,
                              "finding": supported_finding_types,
                              "issue": supported_issue_types}

    @classmethod
    def format_object(cls, object_type, object_subtype, object_json):
        """Return Jira-formatted text describing object.

        Args:
            object_type (str): Must match cls.supported_object_types
            object_subtype (str): Must match for object_type. See class vars.
            object_json (str): Halo object json to be formatted.

        Returns:
            str: Jira-formatted text describing object.
        """
        val = ""
        try:
            val += object_type
            otype = cls.supported_object_types[object_type]
            val += ":{}".format(object_subtype)
            osubtype = otype[object_subtype]
            formatted = osubtype.format(object_json)
        except KeyError:
            log = Logger()
            msg = "Formatter: Unsupported type: {}".format(val)
            log.error(msg)
            return None
        return formatted

    @classmethod
    def format_summary(cls, asset_type, issue_type, asset_described):
        """Format summary string."""
        if asset_type not in cls.supported_asset_types:
            return None
        elif asset_type == "server":
            summary = "Halo detected {} issue in server {}".format(issue_type, asset_described["hostname"])  # NOQA
            return summary
