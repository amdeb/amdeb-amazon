# -*- coding: utf-8 -*-

import cPickle
import logging
_logger = logging.getLogger(__name__)

from ..shared.model_names import (
    PRODUCT_PRODUCT_TABLE,
    MODEL_NAME_FIELD,
    RECORD_ID_FIELD,
    TEMPLATE_ID_FIELD,
    PRODUCT_SKU_FIELD,

    AMAZON_PRODUCT_SYNC_TABLE,
    SYNC_TYPE_FIELD,
    SYNC_DATA_FIELD,
)

from ..shared.sync_operation_types import (
    SYNC_CREATE,
    SYNC_UPDATE,
    SYNC_DELETE,
    SYNC_PRICE,
    SYNC_INVENTORY,
    SYNC_IMAGE,
    SYNC_DEACTIVATE,
    SYNC_RELATION,
)


class ProductSyncCreation(object):
    """
    Insert new sync operations to product sync table
    The header is an object that defines model_name,
    record_id and template_id. It could be a product operation record
    or an Amazon sync record
    """
    def __init__(self, env):
        self._table = env[AMAZON_PRODUCT_SYNC_TABLE]

    def _insert_sync_record(self, header, sync_type, sync_data=None):
        """
        Create a sync operation record
        sync_data can be one of three values:
        False: ignore sync_data
        None: use operation data
        others: use sync data
        """
        sync_record = {
            MODEL_NAME_FIELD: header[MODEL_NAME_FIELD],
            RECORD_ID_FIELD: header[RECORD_ID_FIELD],
            TEMPLATE_ID_FIELD: header[TEMPLATE_ID_FIELD],
            SYNC_TYPE_FIELD: sync_type,
        }

        if sync_data:
            sync_record[SYNC_DATA_FIELD] = sync_data

        record = self._table.create(sync_record)
        log_template = "Create new sync record id {0} for Model: {1}, " \
                       "record id: {2}, sync type: {3}."
        _logger.debug(log_template.format(
            record.id,
            sync_record[MODEL_NAME_FIELD],
            sync_record[RECORD_ID_FIELD],
            sync_record[SYNC_TYPE_FIELD],
        ))

    def insert_create(self, header):
        self._insert_sync_record(header, SYNC_CREATE)

    def insert_price(self, header, price):
        if price >= 0:
            sync_value = cPickle.dumps(price, cPickle.HIGHEST_PROTOCOL)
            self._insert_sync_record(header, SYNC_PRICE, sync_value)
        else:
            log_template = "Price {0} is a negative number for " \
                           "Model: {1}, record id: {2}."
            _logger.warning(log_template.format(
                price,
                header[MODEL_NAME_FIELD],
                header[RECORD_ID_FIELD],
            ))

    def insert_inventory(self, header, inventory):
        if inventory >= 0:
            sync_value = cPickle.dumps(inventory, cPickle.HIGHEST_PROTOCOL)
            self._insert_sync_record(header, SYNC_INVENTORY, sync_value)
        else:
            log_template = "Inventory {0} is a negative number for " \
                           "Model: {1}, record id: {2}. "
            _logger.warning(log_template.format(
                inventory,
                header[MODEL_NAME_FIELD],
                header[RECORD_ID_FIELD],
            ))

    def insert_image(self, header):
        self._insert_sync_record(header, SYNC_IMAGE)

    def insert_update(self, header, write_values):
        if write_values:
            sync_value = cPickle.dumps(
                write_values, cPickle.HIGHEST_PROTOCOL)
            self._insert_sync_record(header, SYNC_UPDATE, sync_value)
        else:
            log_template = "Sync value is empty or None for " \
                           "Model: {1}, record id: {2}."
            _logger.warning(log_template.format(
                header[MODEL_NAME_FIELD],
                header[RECORD_ID_FIELD],
            ))

    def insert_deactivate(self, header):
        self._insert_sync_record(header, SYNC_DEACTIVATE)

    def insert_relation(self, header):
        # the header here should be only for variant
        if header[MODEL_NAME_FIELD] != PRODUCT_PRODUCT_TABLE:
            raise ValueError("Invalid model name value for insert_relation.")

        self._insert_sync_record(header, SYNC_RELATION)

    def insert_amazon_delete(self, amazon_product):
        """
        Insert a delete sync for a product operation object
        """
        product_sku = amazon_product[PRODUCT_SKU_FIELD]
        sync_value = cPickle.dumps(product_sku, cPickle.HIGHEST_PROTOCOL)
        self._insert_sync_record(amazon_product, SYNC_DELETE, sync_value)
