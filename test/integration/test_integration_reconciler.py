from datetime import datetime, timedelta
import jlib
import os


class TestIntegrationReconciler:
    def get_halo_object(self):
        key = os.getenv("HALO_API_KEY")
        secret = os.getenv("HALO_API_SECRET_KEY")
        api_host = os.getenv("HALO_API_HOSTNAME")
        halo_obj = jlib.Halo(key, secret, api_host, 10)
        return halo_obj

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

    def get_reconciler_object(self):
        halo = self.get_halo_object()
        jira = self.get_jira_object()
        dyn_mapping = {}
        static_mapping = {}
        return jlib.Reconciler(halo, jira, dyn_mapping, static_mapping)

    def get_iso_yesterday(self):
        dt_yest = datetime.now() - timedelta(1)
        return dt_yest.isoformat()

    def test_reconcile_create_comment_transition(self):
        reconciler = self.get_reconciler_object()
        target_issue = reconciler.halo.issues.list_all(state=["active",
                                                              "deactivated",
                                                              "missing",
                                                              "retired"],
                                                       since=self.get_iso_yesterday())  # NOQA
        full_issue = reconciler.halo.get_issue_full(target_issue[0]["id"])
        issue_key = reconciler.create(full_issue)
        reconciler.comment(full_issue, issue_key)
        reconciler.change_status(issue_key,
                                 os.getenv("ISSUE_CLOSE_TRANSITION"))
        assert issue_key

    def test_reconcile_create_closed(self):
        reconciler = self.get_reconciler_object()
        target_issue = reconciler.halo.issues.list_all(state=["active",
                                                              "deactivated",
                                                              "missing",
                                                              "retired"],
                                                       since=self.get_iso_yesterday())  # NOQA
        full_issue = reconciler.halo.get_issue_full(target_issue[0]["id"])
        reconciler.create_closed(full_issue,
                                 os.getenv("ISSUE_CLOSE_TRANSITION"))
        assert True
