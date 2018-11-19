"""The Determinator class decides what actions to take WRT Jira tickets."""
from logger import Logger


class Determinator(object):
    """
    Args:
        issue_close_transition (str): This transition will be used to close
            Jira issues.
        issue_status_hard_closed (str): Issues with this status will not be
            reopened. Instead, a new Jira issue will be created.
        issue_reopen_transition (str): Reopened issues will be ceated with this
            status.

    """

    supported_types = ["sva", "csm", "fim", "lids"]

    def __init__(self, issue_status_closed, issue_status_hard_closed,
                 issue_close_transition, issue_reopen_transition):
        self.issue_close_transition = issue_close_transition
        self.issue_status_closed = issue_status_closed
        self.issue_status_hard_closed = issue_status_hard_closed
        self.issue_reopen_transition = issue_reopen_transition
        self.all_closed_statuses = [self.issue_status_closed,
                                    self.issue_status_hard_closed]
        self.logger = Logger()
        return

    def get_disposition(self, halo_issue, jira_tickets):
        """Return action and instructions for handling halo_issue.

        Args:
            halo_issue (dict): Halo issue json from
                cloudpassage.Issue().describe().
            jira_tickets (list): List of Jira tickets relating to halo_issue.

        Returns:
            tuple: (disposition (str), instructions (dict)) where
                disposition may be 'create', 'create_closed', 'comment',
                'change_status', or 'nothing'. Instructions will comtain a
                different structure, depending on the disposition.

        Instructions reference:
            create: None
            create_closed: {'target_status': 'status_name', 'jira_id': 'ticket_id'}
            comment: {'jira_id': 'ticket_id'}
            change_status: {'target_status': 'status_name', 'jira_id': 'ticket_id'}
            nothing: None

        """

        if halo_issue["issue_type"] not in self.supported_types:
            msg = "Unsupported type {}: {}".format(halo_issue["id"],
                                                   halo_issue["issue_type"])
            self.logger.warn(msg)
            result = ("nothing", None)
        elif self.create(halo_issue, jira_tickets):
            msg = "Create issue for {}".format(halo_issue["id"])
            result = ("create", None)
        elif self.create_closed(halo_issue, jira_tickets):
            msg = "Create closed issue for {}".format(halo_issue["id"])
            result = ("create_closed", self.get_transition_instructions("close", jira_tickets))
        elif self.close(halo_issue, jira_tickets):
            msg = "Close issue for {}".format(halo_issue["id"])
            result = ("change_status", self.get_transition_instructions("close", jira_tickets))
        elif self.comment(halo_issue, jira_tickets):
            msg = "Comment issue {}".format(halo_issue["id"])
            result = ("comment", self.comment_instructions(jira_tickets))
        elif self.reopen(halo_issue, jira_tickets):
            msg ="Reopen issue for {}".format(halo_issue["id"])
            result = ("change_status", self.get_transition_instructions("reopen", jira_tickets))
        else:
            i_id = halo_issue["id"]
            msg = "ERROR: Halo issue {} passed through determinator.".format(i_id)
            self.logger.warn(msg)
            result = ("nothing", None)
        self.logger.debug(msg)
        return result

    def get_transition_instructions(self, transition, jira_tickets):
        supported_transitions = {"close": self.issue_close_transition,
                                 "reopen": self.issue_reopen_transition}
        tix = sorted(jira_tickets, key=lambda k: k.fields.updated)
        if tix:
            jira_id = tix[0].key
        else:
            jira_id = ""
        retval = {"transition": supported_transitions[transition],
                  "jira_id": jira_id}
        return retval

    def comment_instructions(self, jira_tickets):
        """Return instructions for commenting on a ticket."""
        jiraz = sorted(jira_tickets, key=lambda k: k.fields.updated)
        return {"jira_id": jiraz[0].key}

    def create(self, halo_issue, jira_tickets):
        """Return True if Halo issue is active and no Jira tickets exist."""
        useable_jira_tix = [x for x in jira_tickets
            if x.fields.status.name != self.issue_status_hard_closed]
        if halo_issue["status"] == "active" and not useable_jira_tix:
            return True

    def create_closed(self, halo_issue, jira_tickets):
        """Return True if Halo issue is resolved and no Jira tickets exist."""
        open_jira_tix = [x for x in jira_tickets
                         if x.fields.status.name
                         not in self.all_closed_statuses]
        if halo_issue["status"] == "resolved" and not open_jira_tix:
            return True

    def close(self, halo_issue, jira_tickets):
        """Return True if open Jira ticket and Halo issue is resolved."""
        elligible_tix = [x for x in jira_tickets
                         if x.fields.status.name
                         not in self.all_closed_statuses]
        if halo_issue["status"] == "resolved" and elligible_tix:
            return True

    def comment(self, halo_issue, jira_tickets):
        """Return true if open Jira ticket and Halo issue is active."""
        elligible_tix = [x for x in jira_tickets
                         if x.fields.status.name
                         not in self.all_closed_statuses]
        if halo_issue["status"] == "active" and elligible_tix:
            return True

    def reopen(self, halo_issue, jira_tickets):
        """Return True if Halo issue is active and Jira ticket is reopenable."""
        reopenable_tix = [x for x in jira_tickets
                          if x.fields.status.name == self.issue_status_closed]
        if halo_issue["status"] == "active" and reopenable_tix:
            return True
