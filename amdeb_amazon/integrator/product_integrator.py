# -*- coding: utf-8 -*-

"""
Event subscribers for product-related operations.
Odoo uses two tables to store product-related data:
product.template and product.product.
We need to subscribe both in write operation.
"""

import cPickle

from ..shared.model_names import (
    PRODUCT_PRODUCT,
    PRODUCT_TEMPLATE,
    PRODUCT_OPERATION_TABLE,
)

from ..shared.record_operations import (
    CREATE_RECORD,
    WRITE_RECORD,
    UNLINK_RECORD,
)

from .event import (
    create_record_event,
    write_record_event,
    unlink_record_event
)

import logging

_logger = logging.getLogger(__name__)


def _create_record(model_name, env, product_id):
    record_values = {
        'record_id': product_id,
        'model_name': model_name,
        'record_operation': CREATE_RECORD,
    }
    model = env[PRODUCT_OPERATION_TABLE]
    record = model.create(record_values)
    return record


@create_record_event(PRODUCT_TEMPLATE)
def create_product_template(env, product_id):
    _logger.debug('entering create_product_template id: {}'.format(product_id))
    record = _create_record(PRODUCT_TEMPLATE, env, product_id)
    _logger.debug('create_product_template created record id: {}'.format(
        record.id))


@create_record_event(PRODUCT_PRODUCT)
def create_product_product(env, product_id):
    _logger.debug('entering create_product_product id: {}'.format(product_id))
    record = _create_record(PRODUCT_PRODUCT, env, product_id)
    _logger.debug('create_product_product created record id: {}'.format(
        record.id))


def _write_record(model_name, env, product_id, values):
    """ Write a product write record for the model name """

    # product_template call write() after it creates a new database record
    # therefore it triggers write event first that should be ignored.
    # ignore a write operation that doesn't have a create operation
    model = env[PRODUCT_OPERATION_TABLE]
    count = model.search([['record_id', '=', product_id]], count=True)
    if not count:
        _logger.debug('write product_id {} in creation, ignore it.'.format(
            product_id))
        return None

    data = cPickle.dumps(values, cPickle.HIGHEST_PROTOCOL)
    record_values = {
        'record_id': product_id,
        'model_name': model_name,
        'record_operation': WRITE_RECORD,
        'operation_data': data,
    }
    record = model.create(record_values)
    return record.id


@write_record_event(PRODUCT_TEMPLATE)
def write_product_template(env, product_id, values):
    _logger.debug('entering write_product_template id: {}, values {}'.format(
        product_id, values))
    record_id = _write_record(PRODUCT_TEMPLATE, env, product_id, values)
    _logger.debug('write_product_template created record id: {}'.format(
        record_id))


@write_record_event(PRODUCT_PRODUCT)
def write_product_product(env, product_id, values):
    _logger.debug('entering write_product_product id: {}, values {}'.format(
        product_id, values))
    record_id = _write_record(PRODUCT_PRODUCT, env, product_id, values)
    _logger.debug('write_product_product created record id: {}'.format(
        record_id))


def _unlink_record(model_name, env, product_id):
    record_values = {
        'record_id': product_id,
        'model_name': model_name,
        'record_operation': UNLINK_RECORD,
    }

    model = env[PRODUCT_OPERATION_TABLE]
    record = model.create(record_values)
    return record.id


@unlink_record_event(PRODUCT_TEMPLATE)
def unlink_product_template(env, product_id):
    _logger.debug('entering unlink_product_template id: {}'.format(product_id))
    record_id = _unlink_record(PRODUCT_TEMPLATE, env, product_id)
    _logger.debug('unlink_product_template created record id: {}'.format(
        record_id))


@unlink_record_event(PRODUCT_PRODUCT)
def unlink_product_product(env, product_id):
    _logger.debug('entering unlink_product_product id: {}'.format(product_id))
    record_id = _unlink_record(PRODUCT_PRODUCT, env, product_id)
    _logger.debug('unlink_product_product created record id: {}'.format(
        record_id))
