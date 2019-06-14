import jlib
import json
import os


here_dir = os.path.abspath(os.path.dirname(__file__))
fixtures_dir = os.path.join(here_dir, "../fixture")


class TestIntegrationMapper:
    def get_json_from_file(self, file_name):
        with open(os.path.join(fixtures_dir, file_name), 'r') as j_f:
            issue = json.load(j_f)
        return issue

    def test_mapper_end_to_end(self):
        dynamic = {"asset_group_name": "jira_field_whatever1assetgroup",
                   "issue_type": "jirafield_issue_type"}
        static = {"jira_field_1": "halo_field_1"}
        asset = self.get_json_from_file("server.json")
        issue = self.get_json_from_file("server_fim_issue_created_describe.json")  # NOQA
        result = jlib.Mapper.map_fields(dynamic, static, asset, issue)
        print(result)
        assert result["jira_field_1"] == "halo_field_1"
        assert result["jirafield_issue_type"] == "fim"

    def test_mapper_end_to_end_2(self):
        """Gentle failure with unrecognized asset"""
        dynamic = {"asset_group_name": "jira_field_whatever1assetgroup",
                   "issue_type": "jirafield_issue_type"}
        static = {"jira_field_1": "halo_field_1"}
        asset = self.get_json_from_file("server.json")
        del asset["hostname"]
        issue = self.get_json_from_file("server_fim_issue_created_describe.json")  # NOQA
        result = jlib.Mapper.map_fields(dynamic, static, asset, issue)
        print(result)
        assert result["jira_field_1"] == "halo_field_1"
        assert result["jirafield_issue_type"] == "fim"

    def test_mapper_end_to_end_3(self):
        """Gentle failure with bad field ref."""
        dynamic = {"asset_group_name": "jira_field_whatever1assetgroup",
                   "issue_type_nonexist": "jirafield_issue_type"}
        static = {"jira_field_1": "halo_field_1"}
        asset = self.get_json_from_file("server.json")
        issue = self.get_json_from_file("server_fim_issue_created_describe.json")  # NOQA
        result = jlib.Mapper.map_fields(dynamic, static, asset, issue)
        print(result)
        assert result["jira_field_1"] == "halo_field_1"

    def test_mapper_missing_attribute_1(self):
        """Test with missing server attribute."""
        dynamic = {"asset_group_name": "jira_field_whatever1assetgroup",
                   "asset_group_path": "dead_field",
                   "issue_type": "jirafield_issue_type",
                   "policy_name": "dead_policy_name_field"}
        static = {"jira_field_1": "halo_field_1"}
        asset = self.get_json_from_file("server_missing_attribute.json")
        issue = self.get_json_from_file("server_sva_issue_created_describe_missing_attribute.json")  # NOQA
        result = jlib.Mapper.map_fields(dynamic, static, asset, issue)
        print(result)
        assert result["jira_field_1"] == "halo_field_1"
        assert result["jirafield_issue_type"] == "sva"
