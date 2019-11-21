from .logger import Logger


class Mapper(object):
    @classmethod
    def map_fields(cls, dynamic_mapping, static_mapping, issue_described):
        if not static_mapping: static_mapping = {}
        if not dynamic_mapping: dynamic_mapping = {}
        result = static_mapping.copy()
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
                    retval[v] = issue[field]
        return retval
