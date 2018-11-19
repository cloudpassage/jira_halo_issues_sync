import jlib
import jira
import json
import os


here_dir = os.path.abspath(os.path.dirname(__file__))
fixtures_dir = os.path.join(here_dir, "../fixture")


class TestIntegrationDetermaintor:
    def generate_halo_server_issue_meta(self, module, action):
        """Return Halo issue for module and action (created, resolved)."""
        if module not in ["csm", "fim", "lids", "sva"]:
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
        test_halo["issue_type"] = "automotive"
        test_jira = []
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("nothing", None)

    def test_integration_determinator_get_disposition_create_csm(self):
        test_halo = self.generate_halo_server_issue_meta("csm", "created")
        test_jira = []
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("create", None)

    def test_integration_determinator_get_disposition_create_fim(self):
        test_halo = self.generate_halo_server_issue_meta("fim", "created")
        test_jira = []
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("create", None)

    def test_integration_determinator_get_disposition_create_lids(self):
        test_halo = self.generate_halo_server_issue_meta("lids", "created")
        test_jira = []
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("create", None)

    def test_integration_determinator_get_disposition_create_sva(self):
        test_halo = self.generate_halo_server_issue_meta("sva", "created")
        test_jira = []
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("create", None)

    def test_integration_determinator_get_disposition_close_csm(self):
        test_halo = self.generate_halo_server_issue_meta("csm", "resolved")
        test_jira = [self.generate_jira_issue("open")]
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("change_status", {'transition': 'close', 'jira_id': 'AB-263'})

    def test_integration_determinator_get_disposition_close_fim(self):
        test_halo = self.generate_halo_server_issue_meta("fim", "resolved")
        test_jira = [self.generate_jira_issue("open")]
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("change_status", {'transition': 'close', 'jira_id': 'AB-263'})


    def test_integration_determinator_get_disposition_close_lids(self):
        test_halo = self.generate_halo_server_issue_meta("lids", "resolved")
        test_jira = [self.generate_jira_issue("open")]
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("change_status", {'transition': 'close', 'jira_id': 'AB-263'})


    def test_integration_determinator_get_disposition_close_sva(self):
        test_halo = self.generate_halo_server_issue_meta("sva", "resolved")
        test_jira = [self.generate_jira_issue("open")]
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("change_status", {'transition': 'close', 'jira_id': 'AB-263'})


    def test_integration_determinator_get_disposition_comment_csm(self):
        test_halo = self.generate_halo_server_issue_meta("csm", "created")
        test_jira = [self.generate_jira_issue("open")]
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("comment", {'jira_id': 'AB-263'})


    def test_integration_determinator_get_disposition_comment_fim(self):
        test_halo = self.generate_halo_server_issue_meta("fim", "created")
        test_jira = [self.generate_jira_issue("open")]
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("comment", {'jira_id': 'AB-263'})

    def test_integration_determinator_get_disposition_comment_lids(self):
        test_halo = self.generate_halo_server_issue_meta("lids", "created")
        test_jira = [self.generate_jira_issue("open")]
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("comment", {'jira_id': 'AB-263'})

    def test_integration_determinator_get_disposition_comment_sva(self):
        test_halo = self.generate_halo_server_issue_meta("sva", "created")
        test_jira = [self.generate_jira_issue("open")]
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("comment", {'jira_id': 'AB-263'})

    def test_integration_determinator_get_disposition_create_closed_csm(self):
        test_halo = self.generate_halo_server_issue_meta("csm", "resolved")
        test_jira = [self.generate_jira_issue("hard_closed")]
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination[0] == "create_closed"
        assert determination[1]["transition"] == "close"

    def test_integration_determinator_get_disposition_create_closed_fim(self):
        test_halo = self.generate_halo_server_issue_meta("fim", "resolved")
        test_jira = [self.generate_jira_issue("hard_closed")]
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination[0] == "create_closed"
        assert determination[1]["transition"] == "close"

    def test_integration_determinator_get_disposition_create_closed_lids(self):
        test_halo = self.generate_halo_server_issue_meta("lids", "resolved")
        test_jira = [self.generate_jira_issue("hard_closed")]
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination[0] == "create_closed"
        assert determination[1]["transition"] == "close"

    def test_integration_determinator_get_disposition_create_closed_sva(self):
        test_halo = self.generate_halo_server_issue_meta("sva", "resolved")
        test_jira = [self.generate_jira_issue("hard_closed")]
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination[0] == "create_closed"
        assert determination[1]["transition"] == "close"

    def test_integration_determinator_get_disposition_reticket_csm(self):
        test_halo = self.generate_halo_server_issue_meta("csm", "created")
        test_jira = [self.generate_jira_issue("hard_closed")]
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("create", None)

    def test_integration_determinator_get_disposition_reticket_fim(self):
        test_halo = self.generate_halo_server_issue_meta("fim", "created")
        test_jira = [self.generate_jira_issue("hard_closed")]
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("create", None)

    def test_integration_determinator_get_disposition_reticket_lids(self):
        test_halo = self.generate_halo_server_issue_meta("lids", "created")
        test_jira = [self.generate_jira_issue("hard_closed")]
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("create", None)

    def test_integration_determinator_get_disposition_reticket_sva(self):
        test_halo = self.generate_halo_server_issue_meta("sva", "created")
        test_jira = [self.generate_jira_issue("hard_closed")]
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("create", None)

    def test_integration_determinator_get_disposition_reopen_csm(self):
        test_halo = self.generate_halo_server_issue_meta("csm", "created")
        test_jira = [self.generate_jira_issue("closed")]
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("change_status", {'transition': 'reopened', 'jira_id': 'AB-263'})

    def test_integration_determinator_get_disposition_reopen_fim(self):
        test_halo = self.generate_halo_server_issue_meta("fim", "created")
        test_jira = [self.generate_jira_issue("closed")]
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("change_status", {'transition': 'reopened', 'jira_id': 'AB-263'})

    def test_integration_determinator_get_disposition_reopen_lids(self):
        test_halo = self.generate_halo_server_issue_meta("lids", "created")
        test_jira = [self.generate_jira_issue("closed")]
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("change_status", {'transition': 'reopened', 'jira_id': 'AB-263'})

    def test_integration_determinator_get_disposition_reopen_sva(self):
        test_halo = self.generate_halo_server_issue_meta("sva", "created")
        test_jira = [self.generate_jira_issue("closed")]
        determinator = jlib.Determinator("closed", "hard_closed", "close",
                                         "reopened")
        determination = determinator.get_disposition(test_halo, test_jira)
        assert determination == ("change_status", {'transition': 'reopened', 'jira_id': 'AB-263'})
