class Mapper(object):
    @classmethod
    def map_fields(cls, dynamic_mapping, static_mapping, asset_described,
                   issue_described):
        result = static_mapping.copy()
        dyn_mapped = cls.get_dynamic_mapping(dynamic_mapping, asset_described,
                                             issue_described)
        result.update(dyn_mapped)
        return result

    @classmethod
    def get_dynamic_mapping(cls, dyn_mapping, asset, issue):
        retval = {}
        asset_type = cls.determine_asset_type(asset)
        server_mapping = {"asset_group_name": "group_name",
                          "asset_group_path": "group_path",
                          "asset_type": asset_type,
                          "server_csp_provider": "csp_provider",
                          "server_csp_account_id": "csp_account_id",
                          "server_csp_instance_id": "csp_instance_id",
                          "server_id": "id",
                          "server_hostname": "hostname",
                          "server_state": "state"}
        issue_mapping = {"issue_critical": "critical",
                         "issue_created_at": "created_at",
                         "issue_rule_key": "rule_key",
                         "issue_type": "issue_type",
                         "issue_id": "id",
                         "issue_policy_name": "policy_name"}
        if asset_type == "server":
            for k, v in dyn_mapping.items():
                if k not in server_mapping:
                    pass
                else:
                    retval[v] = asset[server_mapping[k]]
        for k, v in dyn_mapping.items():
            if k not in issue_mapping:
                pass
            else:
                retval[v] = issue[issue_mapping[k]]
        return retval

    @classmethod
    def determine_asset_type(cls, asset_json):
        if "hostname" in asset_json:
            return "server"
        else:
            return None
