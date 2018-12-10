"""This is for cleaning up the Jira testing issues."""
from jira import JIRA
import os


def main():
    """Be careful with this script. We assume that testing happens in one
    dedicated project... so this script deletes ALL tickets in the project
    defined by ${JIRA_PROJECT_KEY}.
    """
    jira_url = os.getenv("JIRA_API_URL")
    auth_user = os.getenv("JIRA_API_USER")
    auth_token = os.getenv("JIRA_API_TOKEN")
    jira_instance = JIRA(jira_url, basic_auth=(auth_user, auth_token))
    default_project_id = os.getenv("JIRA_PROJECT_KEY")
    search_string = "project = {}".format(default_project_id)
    test_issues = jira_instance.search_issues(search_string)
    for issue in test_issues:
        print("Deleting issue with ID {}...".format(issue.key))
        issue.delete()


if __name__ == "__main__":
    main()
