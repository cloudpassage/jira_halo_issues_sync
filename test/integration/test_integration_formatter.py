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
        formatted = jlib.Formatter.format_object('asset', 'server', data)
        assert formatted is not None

    def test_bad_formatter_asset(self):
        formatted = jlib.Formatter.format_object('asset', 'nope', {})
        assert formatted is None

    def test_formatter_finding_sva(self):
        data = self.load_json_from_file("server_sva_finding_describe.json")
        formatted = jlib.Formatter.format_object('finding', 'sva', data)
        assert formatted is not None

    def test_bad_formatter_finding(self):
        formatted = jlib.Formatter.format_object('finding', 'nope', {})
        assert formatted is None

    def test_formatter_issue_fim(self):
        data = self.load_json_from_file("server_fim_issue_created_describe.json")  # NOQA
        formatted = jlib.Formatter.format_object('issue', 'fim', data)
        assert formatted is not None

    def test_bad_formatter_issue(self):
        formatted = jlib.Formatter.format_object('issue', 'nope', {})
        assert formatted is None

    def test_formatter_summary(self):
        data = self.load_json_from_file("server.json")
        formatted = jlib.Formatter.format_summary('server', 'fim', data)
        assert formatted is not None

    def test_bad_formatter_summary(self):
        formatted = jlib.Formatter.format_summary('nope', 'nope', {})
        assert formatted is None
