from jlib.logger import Logger
from datetime import timedelta
from dateutil.parser import isoparse

def map_fields(dynamic_mapping, static_mapping, issue_described, jira_fields_dict):
    result = {}
    for k, v in static_mapping.items():
        result[jira_fields_dict[k]] = v
    if 'duedate' in result:
        due_date = get_due_date_wrt_first_seen(result, issue_described)
        result['duedate'] = due_date

    dyn_mapped = get_dynamic_mapping(dynamic_mapping, issue_described, jira_fields_dict)
    result.update(dyn_mapped)
    return result

def get_dynamic_mapping(dyn_mapping, issue, jira_fields_dict):
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
                retval[jira_fields_dict[v]] = str(issue[field])
    return retval

def get_due_date_wrt_first_seen(static_mapping, issue):
    first_seen_at = isoparse(issue.get("first_seen_at"))
    due_date_time = int(static_mapping['duedate'])
    return (first_seen_at + timedelta(days=due_date_time)).isoformat()
