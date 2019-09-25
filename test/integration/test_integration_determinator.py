import jlib
import jira
import json
import os


here_dir = os.path.abspath(os.path.dirname(__file__))
fixtures_dir = os.path.join(here_dir, "../fixture")


class TestIntegrationDetermaintor:
    def generate_halo_server_issue_meta(self, module, action):
        """Return Halo issue for module and action (created, resolved)."""
        if module not in ["lids", "csm", "fim", "sva", "sam", "fw", "agent", "image_sva"]:
            raise ValueError("Invalid module %s" % module)
        if action not in ["created", "resolved"]:
            raise ValueError("Invalid action: %s" % action)
        j_file = "server_{}_issue_{}_meta.json".format(module, action)
        with open(os.path.join(fixtures_dir, j_file), 'r') as j_f:
            issue = json.load(j_f)
        return issue

    def generate_jira_issue(self, status):
        """Return Jira issue with status (open, closed, hard_closed)."""
        if status not in ["open", "closed", "hard_closed"]:
            raise ValueError("Invalid status: %s" % status)
        j_file = "jira_issue_{}.json".format(status)
        with open(os.path.join(fixtures_dir, j_file), 'r') as j_f:
            retval = json.load(j_f)
        jira_obj = jira.Issue(None, None, retval)
        return jira_obj

    def test_discard_unsupported_event(self):
        test_halo = self.generate_halo_server_issue_meta("csm", "created")
        test_halo["type"] = "automotive"
        test_jira = []
        determinator = jlib.Determinator("closed", "close", "hard_closed",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("nothing", None)

    def test_integration_determinator_get_disposition_create_csm(self):
        test_halo = self.generate_halo_server_issue_meta("csm", "created")
        test_jira = []
        determinator = jlib.Determinator("closed", "close", "hard_closed",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("create", None)

    def test_integration_determinator_get_disposition_close_csm(self):
        test_halo = self.generate_halo_server_issue_meta("csm", "resolved")
        test_jira = [self.generate_jira_issue("open")]
        determinator = jlib.Determinator("closed", "close", "hard_closed",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("change_status", {'transition': 'close',
                                                   'jira_id': 'AB-263'})

    def test_integration_determinator_get_disposition_comment_csm(self):
        test_halo = self.generate_halo_server_issue_meta("csm", "created")
        test_jira = [self.generate_jira_issue("open")]
        determinator = jlib.Determinator("closed", "close", "hard_closed",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("comment", {'jira_id': 'AB-263'})

    def test_integration_determinator_get_disposition_create_closed_csm(self):
        test_halo = self.generate_halo_server_issue_meta("csm", "resolved")
        test_jira = [self.generate_jira_issue("hard_closed")]
        determinator = jlib.Determinator("closed", "close", "hard_closed",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination[0] == "create_closed"
        assert determination[1]["transition"] == "close"

    def test_integration_determinator_get_disposition_reticket_csm(self):
        test_halo = self.generate_halo_server_issue_meta("csm", "created")
        test_jira = [self.generate_jira_issue("hard_closed")]
        determinator = jlib.Determinator("closed", "close", "hard_closed",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("create", None)

    def test_integration_determinator_get_disposition_reopen_csm(self):
        test_halo = self.generate_halo_server_issue_meta("csm", "created")
        test_jira = [self.generate_jira_issue("closed")]
        determinator = jlib.Determinator("closed", "close", "hard_closed",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("change_status", {'transition': 'reopened',
                                                   'jira_id': 'AB-263'})
