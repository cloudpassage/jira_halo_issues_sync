import jlib
import json
import os


here_dir = os.path.abspath(os.path.dirname(__file__))
fixtures_dir = os.path.join(here_dir, "../fixture")


class TestIntegrationFormatterFindingCSM:
    def generate_halo_finding(self):
        """Return Halo finding json."""
        file_name = "server_csm_finding_describe.json"
        with open(os.path.join(fixtures_dir, file_name), 'r') as j_f:
            issue = json.load(j_f)
        return issue

    def test_format_end_to_end(self):
        issue_json = self.generate_halo_finding()
        formatter = jlib.FormatterFindingCSM()
        result = formatter.format(issue_json)
        print(result)
        assert len(result.splitlines()) == 3
