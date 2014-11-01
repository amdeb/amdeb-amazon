# -*- coding: utf-8 -*-

"""
    Intercept record change event by replacing Odoo record change functions
    with new functions. A new functions calls an original one and fires
    an event. The new function signatures are copied from openerp/models.py
"""

from openerp import models, api

from ..shared import utility
from .event import (create_record_event,
                    write_record_event,
                    unlink_record_event)

import logging

_logger = logging.getLogger(__name__)

original_create = models.BaseModel.create
original_write = models.BaseModel.write
original_unlink = models.BaseModel.unlink


@api.model
@api.returns('self', lambda value: value.id)
def create(self, values):
    _logger.debug("In create record for model: {}".format(
        self._name, values))

    record = original_create(self, values)
    create_record_event.fire(self._name, record.id)
    return record

models.BaseModel.create = create


@api.multi
def write(self, values):
    _logger.debug("In write record for model: {} ids: {}".format(
        self._name, self._ids))

    original_write(self, values)
    for record_id in self._ids:
        write_record_event.fire(self._name, record_id, values)

    return True

models.BaseModel.write = write


def unlink(self, cr, uid, ids, context=None):
    _logger.debug("In unlink record for model: {} ids: {}".format(
        self._name, ids))

    original_unlink(self, cr, uid, ids, context=context)
    if not utility.is_sequence(ids):
        ids = [ids]
    for record_id in ids:
        unlink_record_event.fire(self._name, record_id)

    return True

models.BaseModel.unlink = unlink
