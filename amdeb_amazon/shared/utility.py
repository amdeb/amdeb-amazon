# -*- coding: utf-8 -*-

from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from .model_names import WRITE_FIELD_NAMES_FIELD

MWS_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
FIELD_NAME_DELIMITER = ', '


def is_sequence(subject):
    """find out if the subject is a sequence"""
    return hasattr(subject, '__iter__')


# there maybe some arguments when used as field default value
def field_utcnow(*args):
    """ Return the current UTC day and time in the format expected by the ORM.
        This function may be used to compute default values.
    """
    return datetime.utcnow().strftime(DATETIME_FORMAT)


def get_field_names(record):
    field_names = record[WRITE_FIELD_NAMES_FIELD]
    if field_names:
        data = set(field_names.split(FIELD_NAME_DELIMITER))
    else:
        data = set()
    return data
