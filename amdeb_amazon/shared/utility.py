# -*- coding: utf-8 -*-


def is_sequence(subject):
    """find out if the subject is a sequence"""
    return hasattr(subject, '__iter__')
