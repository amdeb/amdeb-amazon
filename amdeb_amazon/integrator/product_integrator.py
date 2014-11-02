# -*- coding: utf-8 -*-

"""
Event subscribers for product-related operations.
Odoo uses two tables to store product-related data:
product.template and product.product.
We need to subscribe both in write operation.
"""

from ..shared.model_names import (
    PRODUCT_PRODUCT,
    PRODUCT_TEMPLATE,
    AMDEB_PRODUCT_OPERATION
)

from .event import (
    create_record_event,
    write_record_event,
    unlink_record_event
)

import logging

_logger = logging.getLogger(__name__)


@create_record_event(PRODUCT_PRODUCT)
def create_product_product(env, id):
    _logger.debug('entering create_product_product id: {}'.format(id))

    values = {
        'record_id': id,
        'model_name': PRODUCT_PRODUCT,
        'record_operation': 'create_record',
    }

    model = env[AMDEB_PRODUCT_OPERATION]
    record = model.create(values)

    _logger.debug('created {} record id: {} values: {}'.format(
        AMDEB_PRODUCT_OPERATION, record.id, values))


@write_record_event(PRODUCT_TEMPLATE)
def write_product_template(env, id, values):
    _logger.debug('write product_template id: {}, values: {}'.format(
        id, values)
    )


@write_record_event(PRODUCT_PRODUCT)
def write_product_product(env, id, values):
    _logger.debug('write product_product id: {}, values: {}'.format(id, values))


@unlink_record_event(PRODUCT_PRODUCT)
def unlink_product_product(env, id):
    _logger.debug('unlink product_product id: {}'.format(id))
