# -*- coding: utf-8 -*-

from .event import (create_record_event,
                    write_record_event,
                    unlink_record_event)

import logging

_logger = logging.getLogger(__name__)

PRODUCT_TEMPLATE_MODEL_NAME = 'product.template'
PRODUCT_PRODUCT_MODEL_NAME = 'product.product'


@create_record_event(PRODUCT_TEMPLATE_MODEL_NAME)
def create_product_template(id):
    _logger.debug('create product template id: {}', id)


@write_record_event(PRODUCT_TEMPLATE_MODEL_NAME)
def write_product_template(id, values):
    _logger.debug('write product template id: {}, values: {}', id, values)


@unlink_record_event(PRODUCT_TEMPLATE_MODEL_NAME)
def unlink_product_template(id):
    _logger.debug('unlink product template id: {}', id)


@create_record_event(PRODUCT_PRODUCT_MODEL_NAME)
def create_product(id):
    _logger.debug('create product id: {}', id)


@write_record_event(PRODUCT_PRODUCT_MODEL_NAME)
def write_product(id, values):
    _logger.debug('write product id: {}, values: {}', id, values)


@unlink_record_event(PRODUCT_PRODUCT_MODEL_NAME)
def unlink_product(id):
    _logger.debug('unlink product id: {}', id)