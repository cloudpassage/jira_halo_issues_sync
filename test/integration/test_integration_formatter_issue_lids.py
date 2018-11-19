import jlib
import json
import os


here_dir = os.path.abspath(os.path.dirname(__file__))
fixtures_dir = os.path.join(here_dir, "../fixture")


class TestIntegrationFormatterIssueLIDS:
    def generate_halo_issue_meta(self):
        """Return Halo issue json."""
        file_name = "server_lids_issue_created_describe.json"
        with open(os.path.join(fixtures_dir, file_name), 'r') as j_f:
            issue = json.load(j_f)
        return issue

    def test_format_end_to_end(self):
        issue_json = self.generate_halo_issue_meta()
        formatter = jlib.FormatterIssueLIDS()
        result = formatter.format(issue_json)
        print(result)
        assert len(result.splitlines()) == 19
