import os
import uuid

import jlib


class TestIntegrationJiraLocal:
    def get_jira_object(self):
        url = os.getenv("JIRA_API_URL")
        user = os.getenv("JIRA_API_USER")
        token = os.getenv("JIRA_API_TOKEN")
        issue_field = os.getenv("JIRA_ISSUE_ID_FIELD")
        project_id = os.getenv("JIRA_PROJECT_KEY")
        default_issue_type = os.getenv("JIRA_ISSUE_TYPE")
        jira_obj = jlib.JiraLocal(url, user, token, issue_field, project_id,
                                  default_issue_type)
        return jira_obj

    def test_create_transition_search_issue(self):
        jira_obj = self.get_jira_object()
        halo_issue_id = str(uuid.uuid1())
        summary = "CI process test issue (test_create_transition_issue)"
        description = "nothing"
        new_issue_key = jira_obj.create_jira_issue(summary, description,
                                                   halo_issue_id)
        comment_text = "Hello World"
        jira_obj.comment_jira_issue(new_issue_key, comment_text)
        jira_obj.jira_issue_transition(new_issue_key, "Close")
        issues_queried = jira_obj.get_jira_issues_for_halo_issue(halo_issue_id)
        assert issues_queried

    def test_create_issue_fields_mismatch(self):
        jira_obj = self.get_jira_object()
        halo_issue_id = str(uuid.uuid1())
        summary = "CI process test issue (test_create_transition_issue)"
        description = "nothing"
        field_mapping = {"DoesnotExist": "ever"}
        x = jira_obj.create_jira_issue(summary, description, halo_issue_id,
                                       field_mapping)
        assert x

    def test_fix_metadata_fields(self):
        jira_fields = [{u'clauseNames': [u'cf[900500]', u'Closed Date'],
                        u'custom': True,
                        u'id': u'customfield_900500',
                        u'key': u'customfield_900500',
                        u'name': u'Closed Date',
                        u'navigable': True,
                        u'orderable': True,
                        u'customId': 900500,
                        u'searchable': True},
                       {u'clauseNames': [u'due', u'duedate'],
                        u'custom': False,
                        u'id': u'duedate',
                        u'key': u'duedate',
                        u'name': u'Due date',
                        u'navigable': True,
                        u'orderable': True,
                        u'schema': {u'system': u'duedate', u'type': u'date'},
                        u'searchable': True}]
        desired_mapping = {"Closed Date": "nowish",
                           "Due date": "thenish",
                           "Not gonna map": "something completely_different"}
        control = {"customfield_900500": "nowish", "duedate": "thenish"}
        result = jlib.JiraLocal.fix_meta_fields(jira_fields, desired_mapping)
        print(result[1])
        assert control == result[0]
