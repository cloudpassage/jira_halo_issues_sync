from .logger import Logger


class Mapper(object):
    @classmethod
    def map_fields(cls, dynamic_mapping, static_mapping, issue_described):
        result = static_mapping.copy()
        dyn_mapped = cls.get_dynamic_mapping(dynamic_mapping, issue_described)
        result.update(dyn_mapped)
        return result

    @classmethod
    def get_dynamic_mapping(cls, dyn_mapping, issue):
        logger = Logger()
        retval = {}

        issue_mapping = {"issue_name": "name",
                         "issue_source": "source",
                         "issue_type": "type",
                         "issue_critical": "critical",
                         "issue_first_seen_at": "first_seen_at",
                         "issue_last_seen_at": "last_seen_at",
                         "issue_resolved_at": "resolved_at",
                         "issue_status": "status",
                         "issue_policy_name": "policy_name",
                         "issue_csp_rule_id": "csp_rule_id",
                         "issue_asset_id": "asset_id",
                         "issue_asset_name": "asset_name",
                         "issue_asset_type": "asset_type",
                         "issue_group_name": "group_name",
                         "issue_csp_account_type": "csp_account_type",
                         "issue_csp_account_id": "csp_account_id",
                         "issue_csp_account_name": "csp_account_name",
                         "issue_csp_region": "csp_region",
                         "issue_csp_service_type": "csp_service_type",
                         "issue_csp_resource_id": "csp_resource_id"}

        for k, v in dyn_mapping.items():
            if k not in issue_mapping:
                pass
            elif issue_mapping[k] not in issue:
                msg = "Mapper: Unable to map {} for {}".format(k, issue["id"])
                logger.warn(msg)
                pass
            else:
                retval[v] = issue[issue_mapping[k]]
        return retval
