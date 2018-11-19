import jlib
import json
import os


here_dir = os.path.abspath(os.path.dirname(__file__))
fixtures_dir = os.path.join(here_dir, "../fixture")


class TestIntegrationFormatterFindingLIDS:
    def generate_halo_finding(self):
        """Return Halo event json."""
        file_name = "server_lids_finding_event_describe.json"
        with open(os.path.join(fixtures_dir, file_name), 'r') as j_f:
            issue = json.load(j_f)
        return issue

    def test_format_end_to_end(self):
        event_json = self.generate_halo_finding()
        formatter = jlib.FormatterFindingLIDS()
        result = formatter.format(event_json)
        print(result)
        assert len(result.splitlines()) == 4
