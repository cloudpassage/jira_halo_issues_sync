from .logger import Logger
from datetime import timedelta
import dateutil.parser


class Mapper(object):
    @classmethod
    def map_fields(cls, dynamic_mapping, static_mapping, issue_described):
        if not static_mapping: static_mapping = {}
        if not dynamic_mapping: dynamic_mapping = {}
        result = static_mapping.copy()
        if 'duedate' in result:
            due_date = cls.get_due_date_wrt_first_seen(result, issue_described)
            result['duedate'] = due_date

        dyn_mapped = cls.get_dynamic_mapping(dynamic_mapping, issue_described)
        result.update(dyn_mapped)
        return result

    @classmethod
    def get_dynamic_mapping(cls, dyn_mapping, issue):
        logger = Logger()
        retval = {}

        for k, v in dyn_mapping.items():
            obj_type, field = k.split('.')
            if obj_type == "issue":
                if field not in issue:
                    msg = "Mapper: Unable to map {} for {}".format(k, issue["id"])
                    logger.warn(msg)
                    pass
                else:
                    retval[v] = str(issue[field])
        return retval

    @classmethod
    def get_due_date_wrt_first_seen(cls, static_mapping, issue):
        first_seen_at = dateutil.parser.parse(issue.get("first_seen_at"))
        due_date_time = int(static_mapping['duedate'])
        return (first_seen_at + timedelta(days=due_date_time)).isoformat()
