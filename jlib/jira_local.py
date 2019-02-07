from jira import JIRA
from jira.exceptions import JIRAError

from .logger import Logger


class JiraLocal(object):
    """Manage interactions with Jira.

    Args:
        jira_url (str): protocol and hostname for Jira instance.
            (https://jira.mydomain.com)
        auth_user (str): Username corresponding to auth token.
        auth_token (str): Jira auth token
        issue_id_field (str): Halo issue ID field
        project_id (str): Jira project ID for newly-created issues
        default_issue_type (str): Type name for newly-created issues
    """
    def __init__(self, jira_url, auth_user, auth_token, issue_id_field,
                 default_project_id, default_issue_type):
        self.jira_instance = JIRA(jira_url, basic_auth=(auth_user, auth_token))
        self.issue_id_field = issue_id_field
        self.default_project_id = default_project_id
        self.default_issue_type = default_issue_type
        self.log = Logger()
        return

    def get_jira_issues_for_halo_issue(self, issue_id):
        """Return a list of all Jira issues existing for Halo issue ID.

        Args:
            issue_id (str): Issue ID for Halo issue.


        Returns:
            list: List of all Jira issues associated with Halo issue ID.
        """
        search_string = '"{}"~{}'.format(self.issue_id_field, issue_id)
        results = self.jira_instance.search_issues(search_string)
        return results

    def create_jira_issue(self, summary, description, halo_issue_id,
                          field_mapping={}):
        """Create a Jira issue, return issue ID.

        Args:
            summary (str): Summary for new issue.
            description (str): Description for new issue.
            halo_issue_id (str): Issue ID for Halo issue.
            field_mapping (dict): Mapping for populating issue fields.

        Returns:
            str: Jira issue ID
        """
        base_fields = {self.issue_id_field: halo_issue_id}
        field_mapping.update(base_fields)
        new_issue = self.jira_instance.create_issue(
                project=self.default_project_id,
                issuetype={'name': self.default_issue_type},
                summary=summary, description=description)
        new_issue_fields = [x for x in self.jira_instance.fields()]
        try:
            fixed_fields, errors = self.fix_meta_fields(new_issue_fields,
                                                        field_mapping)
            if errors:
                msg = ("Failed to map fields for Jira issue: "
                       "{}".format(", ".join(errors)))
                self.log.error(msg)
            new_issue.update(**fixed_fields)
        except JIRAError as e:
            tried = ", ".join([x for x in field_mapping.keys()])
            allowed = " | ".join(["{} or {}".format(x["id"], x["name"])
                                  for x in new_issue_fields])
            msg = ("Failed to update fields on Jira issue {}. "
                   "Tried: {} Allowed: {} Error message: "
                   "{}".format(new_issue.key, tried, allowed, e))
            self.log.error(msg)
            raise e
        return new_issue.key

    @classmethod
    def fix_meta_fields(cls, allowed, desired):
        """Return a dictionary that's usable for updating fields in Jira.

        We go through the list of allowed fields (by ID), then by name,
        populating the result set. An error message is logged for each field
        that is not map-able.

        Args:
            allowed (list): List of dictionaries from the Jira ticket,
                describing valid fields.
            desired (dict): Dictionary of desired values for insertion into
                ticket.

        Returns:
            tuple: (dict: Dictionary ready for updating Jira fields.,
                list: Fields that didn't map.)
        """

        results = {}
        bad_fields = []
        valid_ids = {x["id"] for x in allowed}
        by_field_name = {x["name"]: x["id"] for x in allowed}
        for k, v in list(desired.items()):
            if k in valid_ids:
                results[k] = v
            elif k in by_field_name:
                results[by_field_name[k]] = v
            else:
                bad_fields.append(k)
        return results, bad_fields

    def comment_jira_issue(self, issue_id, comment):
        """Add a comment to a Jira issue."""
        self.jira_instance.add_comment(issue_id, comment)
        return

    def jira_issue_transition(self, issue_id, transition):
        """Change the status of a Jira issue."""
        issue = self.jira_instance.issue(issue_id)
        transitions = self.jira_instance.transitions(issue)
        options = [(t['id'], t['name']) for t in transitions
                   if t['name'] == transition]
        if not options:
            allowed_transitions = ", ".join([x["name"] for x in transitions])
            msg = "Unable to transition {} via {}.".format(issue_id,
                                                           transition)
            msg += " Allowed transitions: {}".format(allowed_transitions)
            self.log.error(msg)
        else:
            self.jira_instance.transition_issue(issue, options[0][0])
        return
