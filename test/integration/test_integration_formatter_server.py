import jlib
import json
import os


here_dir = os.path.abspath(os.path.dirname(__file__))
fixtures_dir = os.path.join(here_dir, "../fixture")


class TestIntegrationFormatterServer:
    def generate_halo_server_meta(self):
        """Return Halo server json."""
        with open(os.path.join(fixtures_dir, "server.json"), 'r') as j_f:
            issue = json.load(j_f)
        return issue

    def test_format_end_to_end(self):
        server_json = self.generate_halo_server_meta()
        formatter = jlib.FormatterServer()
        result = formatter.format(server_json)
        with open(os.path.join(fixtures_dir, "server.txt"), "r") as f:
            control = f.read()
        print(result)
        assert len(result.splitlines()) == len(control.splitlines())
