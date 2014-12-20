# -*- coding: utf-8 -*-

import cPickle
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

from amdeb_amazon.shared.model_names import (
    PRODUCT_PRODUCT_TABLE, MODEL_NAME_FIELD,
    RECORD_ID_FIELD, TEMPLATE_ID_FIELD, PRODUCT_SKU_FIELD,

    AMAZON_PRODUCT_SYNC_TABLE, SYNC_TYPE_FIELD, SYNC_DATA_FIELD,
    SYNC_CREATION_TIMESTAMP_FIELD, SYNC_STATUS_FIELD,
    SYNC_CHECK_STATUS_COUNT_FILED, AMAZON_MESSAGE_CODE_FIELD,
    AMAZON_RESULT_DESCRIPTION_FIELD
)

from amdeb_amazon.shared.sync_status import (
    SYNC_NEW, SYNC_PENDING, SYNC_ERROR,
    AMAZON_PROCESS_DONE_STATUS,
)

from amdeb_amazon.shared.sync_operation_types import (
    SYNC_CREATE, SYNC_UPDATE, SYNC_DELETE, SYNC_PRICE,
    SYNC_INVENTORY, SYNC_IMAGE, SYNC_DEACTIVATE, SYNC_RELATION,
)

_UNLINK_DAYS = 100
_ARCHIVE_DAYS = 5
_ARCHIVE_CHECK_COUNT = 100
_ARCHIVE_CODE = "Timeout"
_ARCHIVE_MESSAGE = "Pending more than {0} days and {1} checks".format(
    _ARCHIVE_DAYS, _ARCHIVE_CHECK_COUNT
)


class ProductSyncAccess(object):
    """
    Provide methods for accessing Amazon product sync table
    The header is an object that defines model_name,
    record_id and template_id. It could be a product operation record
    or an Amazon sync record
    """
    def __init__(self, env):
        self._table = env[AMAZON_PRODUCT_SYNC_TABLE]

    def _insert(self, header, sync_type, sync_data=None):
        """
        Insert a new sync operation record.
        """
        values = {
            MODEL_NAME_FIELD: header[MODEL_NAME_FIELD],
            RECORD_ID_FIELD: header[RECORD_ID_FIELD],
            TEMPLATE_ID_FIELD: header[TEMPLATE_ID_FIELD],
            SYNC_TYPE_FIELD: sync_type,
        }

        if sync_data:
            values[SYNC_DATA_FIELD] = sync_data

        record = self._table.create(values)
        log_template = "Create new sync record id {0} for Model: {1}, " \
                       "record id: {2}, sync type: {3}."
        _logger.debug(log_template.format(
            record.id, values[MODEL_NAME_FIELD],
            values[RECORD_ID_FIELD], values[SYNC_TYPE_FIELD]))

    def insert_create(self, header):
        self._insert(header, SYNC_CREATE)

    def insert_price(self, header, price):
        if price >= 0:
            sync_value = cPickle.dumps(price, cPickle.HIGHEST_PROTOCOL)
            self._insert(header, SYNC_PRICE, sync_value)
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
            self._insert(header, SYNC_INVENTORY, sync_value)
        else:
            log_template = "Inventory {0} is a negative number for " \
                           "Model: {1}, record id: {2}. "
            _logger.warning(log_template.format(
                inventory,
                header[MODEL_NAME_FIELD],
                header[RECORD_ID_FIELD],
            ))

    def insert_image(self, header):
        self._insert(header, SYNC_IMAGE)

    def insert_update(self, header, write_values):
        if write_values:
            dumped = cPickle.dumps(write_values, cPickle.HIGHEST_PROTOCOL)
            self._insert(header, SYNC_UPDATE, dumped)
        else:
            log_template = "Sync value is empty or None for " \
                           "Model: {1}, record id: {2}."
            _logger.warning(log_template.format(
                header[MODEL_NAME_FIELD],
                header[RECORD_ID_FIELD]))

    def insert_deactivate(self, header):
        self._insert(header, SYNC_DEACTIVATE)

    def insert_relation(self, header):
        # the header here should be only for variant
        if header[MODEL_NAME_FIELD] != PRODUCT_PRODUCT_TABLE:
            raise ValueError("Invalid model name value for insert_relation.")

        self._insert(header, SYNC_RELATION)

    def insert_delete(self, amazon_product):
        """
        Insert a delete sync for an amazon product object that
        has a SKU field used by Amazon API
        """
        product_sku = amazon_product[PRODUCT_SKU_FIELD]
        sync_value = cPickle.dumps(product_sku, cPickle.HIGHEST_PROTOCOL)
        self._insert(amazon_product, SYNC_DELETE, sync_value)

    def get_updates(self):
        search_domain = [
            (SYNC_STATUS_FIELD, '=', SYNC_NEW),
            (SYNC_TYPE_FIELD, '=', SYNC_UPDATE)
        ]
        return self._table.search(search_domain)

    def get_pending(self):
        # get pending in the ascending id order to
        # process the newest sync first.
        search_domain = [(SYNC_STATUS_FIELD, '=', SYNC_PENDING)]
        return self._table.search(search_domain, order="id asc")

    def get_completed(self):
        search_domain = [
            (SYNC_STATUS_FIELD, '=', SYNC_PENDING),
            (AMAZON_MESSAGE_CODE_FIELD, '=', AMAZON_PROCESS_DONE_STATUS)
        ]
        return self._table.search(search_domain)

    def archive_old(self):
        _logger.debug("Enter ProductSyncAccess archive_old()")
        now = datetime.utcnow()
        archive_date = now - timedelta(days=_ARCHIVE_DAYS)
        archive_date_str = archive_date.strftime(DATETIME_FORMAT)
        archive_records = self._table.search([
            (SYNC_CREATION_TIMESTAMP_FIELD, '<', archive_date_str),
            (SYNC_STATUS_FIELD, '=', SYNC_PENDING),
            (SYNC_CHECK_STATUS_COUNT_FILED, '>=', _ARCHIVE_CHECK_COUNT)
        ])
        if archive_records:
            archive_status = {
                SYNC_STATUS_FIELD: SYNC_ERROR,
                AMAZON_MESSAGE_CODE_FIELD: _ARCHIVE_CODE,
                AMAZON_RESULT_DESCRIPTION_FIELD: _ARCHIVE_MESSAGE
            }
            archive_records.write(archive_status)
        count = len(archive_records)
        _logger.debug("archived {} old amazon sync records".format(
            count
        ))

    def cleanup(self):
        _logger.debug("Enter ProductSyncAccess cleanup()")
        now = datetime.utcnow()
        unlink_date = now - timedelta(days=_UNLINK_DAYS)
        unlink_date_str = unlink_date.strftime(DATETIME_FORMAT)
        unlink_records = self._table.search([
            (SYNC_CREATION_TIMESTAMP_FIELD, '<', unlink_date_str)
        ])
        count = len(unlink_records)
        if unlink_records:
            unlink_records.unlink()

        _logger.debug("deleted {} old amazon sync records".format(
            count
        ))
