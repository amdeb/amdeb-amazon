# -*- coding: utf-8 -*-

from datetime import datetime

from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


def is_sequence(subject):
    """find out if the subject is a sequence"""
    return hasattr(subject, '__iter__')


# there maybe some arguments when used as field default value
def field_utcnow(*args):
    """ Return the current UTC day and time in the format expected by the ORM.
        This function may be used to compute default values.
    """
    return datetime.utcnow().strftime(DATETIME_FORMAT)
