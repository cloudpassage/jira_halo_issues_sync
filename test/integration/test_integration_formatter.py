import jlib
import json
import os


here_dir = os.path.abspath(os.path.dirname(__file__))
fixtures_dir = os.path.join(here_dir, "../fixture")


class TestIntegrationFormatter:
    def load_json_from_file(self, file_name):
        """Return Halo finding json."""
        with open(os.path.join(fixtures_dir, file_name), 'r') as j_f:
            issue = json.load(j_f)
        return issue

    def test_formatter_asset_server(self):
        data = self.load_json_from_file("server.json")
        formatted = jlib.Formatter.format_object('server', data)
        assert formatted is not None

    def test_formatter_finding_sva(self):
        data = self.load_json_from_file("server_sva_finding_describe.json")
        formatted = jlib.Formatter.format_object('finding', data)
        assert formatted is not None

    def test_formatter_issue_fim(self):
        data = self.load_json_from_file("server_fim_issue_created_describe.json")  # NOQA
        formatted = jlib.Formatter.format_object('issue', data)
        assert formatted is not None

    def test_formatter_summary(self):
        data = self.load_json_from_file("server_csm_issue_created_describe.json")
        formatted = jlib.Formatter.format_summary(data)
        assert formatted is not None
