"""Base class for formatters."""
import sys


class BaseFormatter(object):
    @classmethod
    def format_field(cls, asset_json, field_name):
        """Format field by name.

        For now, we only support top-level string-type key/value pairs.

        """
        result = ""
        field_value = asset_json[field_name]
        if isinstance(field_value, basestring):
            result = "{}: {}".format(field_name, field_value)
        elif cls.is_a_list_of_strings(field_value):
            result = "{}:\n {}\n".format(field_name,
                                         cls.format_list_of_strings(field_value))  # NOQA
        return result

    @classmethod
    def format(cls, object_json):
        """Return a Jira-formatted representation of an SVA issue."""
        result = cls.format_header(object_json)
        fields = sorted([cls.format_field(object_json, field_name)
                         for field_name in object_json.keys()])
        result += "\n".join([field for field in fields if field != ""])
        return result

    @classmethod
    def format_list_of_strings(cls, field_value):
        return "\n".join(["* {}".format(x) for x in sorted(field_value)])

    @classmethod
    def is_a_list_of_strings(cls, field_value):
        """Return True if field_value is a list of strings, else False."""
        if not isinstance(field_value, list):
            return False
        if [x for x in field_value if not cls.is_it_a_string(x)]:
            return False
        return True

    @classmethod
    def is_it_a_string(cls, sample):
        """Return boolean True if ``sample`` is a string, else return False.

        This will ease transition to Py3.
        """

        if sys.version_info < (3, 0):
            return True if isinstance(sample, basestring) else False  # NOQA: F821
        else:
            return True if isinstance(sample, (str, bytes)) else False
