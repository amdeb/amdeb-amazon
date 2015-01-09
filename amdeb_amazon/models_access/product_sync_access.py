# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import logging

from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

from ..shared.model_names import (
    MODEL_NAME_FIELD, RECORD_ID_FIELD, TEMPLATE_ID_FIELD,
    AMAZON_PRODUCT_SYNC_TABLE, SYNC_TYPE_FIELD, WRITE_FIELD_NAMES_FIELD,
    PRODUCT_CREATE_DATE_FIELD, SYNC_STATUS_FIELD,
    SYNC_CHECK_STATUS_COUNT_FILED, AMAZON_MESSAGE_CODE_FIELD,
    AMAZON_RESULT_DESCRIPTION_FIELD, AMAZON_REQUEST_TIMESTAMP_FIELD,
)
from ..shared.sync_status import (
    SYNC_NEW, SYNC_PENDING, SYNC_ERROR,
    AMAZON_PROCESS_DONE_STATUS, SYNC_SUCCESS,
)
from ..shared.sync_operation_types import (
    SYNC_CREATE, SYNC_UPDATE, SYNC_DELETE, SYNC_PRICE,
    SYNC_INVENTORY, SYNC_IMAGE, SYNC_DEACTIVATE, SYNC_RELATION,
)
from ..shared.utility import field_utcnow

_UNLINK_DAYS = 100
_ARCHIVE_DAYS = 5
_ARCHIVE_CHECK_COUNT = 100
_ARCHIVE_CODE = "Timeout"
_ARCHIVE_MESSAGE = "Pending more than {0} days and {1} checks".format(
    _ARCHIVE_DAYS, _ARCHIVE_CHECK_COUNT
)

_logger = logging.getLogger(__name__)


class ProductSyncAccess(object):
    """
    Provide methods for accessing Amazon product sync table
    The header is an object that defines model_name,
    record_id and template_id. It could be a product operation record
    or an Amazon sync record
    """
    def __init__(self, env):
        self._table = env[AMAZON_PRODUCT_SYNC_TABLE]

    def _insert(self, header, sync_type, write_field_names=None):
        """
        Insert a new sync operation record.
        """

        values = {
            MODEL_NAME_FIELD: header[MODEL_NAME_FIELD],
            RECORD_ID_FIELD: header[RECORD_ID_FIELD],
            TEMPLATE_ID_FIELD: header[TEMPLATE_ID_FIELD],
            SYNC_TYPE_FIELD: sync_type,
        }
        if write_field_names:
            values[WRITE_FIELD_NAMES_FIELD] = write_field_names
        log_template = "Create new sync record for Model: {0}, " \
                       "record id: {1}, sync type: {2}."
        _logger.debug(log_template.format(
            values[MODEL_NAME_FIELD],
            values[RECORD_ID_FIELD],
            values[SYNC_TYPE_FIELD]))
        self._table.create(values)

    def insert_create_if_new(self, header):
        search_domain = [
            (MODEL_NAME_FIELD, '=', header[MODEL_NAME_FIELD]),
            (RECORD_ID_FIELD, '=', header[RECORD_ID_FIELD]),
            (SYNC_STATUS_FIELD, '=', SYNC_NEW),
            (SYNC_TYPE_FIELD, '=', SYNC_CREATE),
        ]
        records = self._table.search(search_domain)
        if records:
            log_template = "Create sync exists for template {}. Skip it."
            _logger.debug(log_template.format(header))
        else:
            self.insert_create(header)

    def insert_create(self, header):
        self._insert(header, SYNC_CREATE)

    def insert_price(self, header):
        self._insert(header, SYNC_PRICE)

    def insert_inventory(self, header):
        self._insert(header, SYNC_INVENTORY)

    def insert_image(self, header):
        self._insert(header, SYNC_IMAGE)

    def insert_update(self, header, write_field_names):
        self._insert(header, SYNC_UPDATE, write_field_names)

    def insert_deactivate(self, header):
        self._insert(header, SYNC_DEACTIVATE)

    def insert_relation(self, header):
        """
        Create sync relation for a product variant
        """
        self._insert(header, SYNC_RELATION)

    def insert_delete(self, amazon_product):
        """
        Insert a delete sync for an amazon product object that
        has a SKU field used by Amazon API
        """
        self._insert(amazon_product, SYNC_DELETE)

    def _get_new_syncs(self, sync_type):
        search_domain = [
            (SYNC_STATUS_FIELD, '=', SYNC_NEW),
            (SYNC_TYPE_FIELD, '=', sync_type)
        ]
        return self._table.search(search_domain)

    def get_new_creates(self):
        return self._get_new_syncs(SYNC_CREATE)

    def get_new_updates(self):
        return self._get_new_syncs(SYNC_UPDATE)

    def get_new_prices(self):
        return self._get_new_syncs(SYNC_PRICE)

    def get_new_inventories(self):
        return self._get_new_syncs(SYNC_INVENTORY)

    def get_new_imagines(self):
        return self._get_new_syncs(SYNC_IMAGE)

    def get_pending(self):
        # get pending in the ascending id order to
        # process the newest sync first.
        search_domain = [(SYNC_STATUS_FIELD, '=', SYNC_PENDING)]
        return self._table.search(search_domain, order="id asc")

    def get_done(self):
        search_domain = [
            (SYNC_STATUS_FIELD, '=', SYNC_PENDING),
            (AMAZON_MESSAGE_CODE_FIELD, '=', AMAZON_PROCESS_DONE_STATUS)
        ]
        return self._table.search(search_domain)

    @staticmethod
    def update_sync_new_status(records, sync_status):
        records.write(sync_status)

    @staticmethod
    def update_sync_new_exception(records, ex):
        sync_status = {
            SYNC_STATUS_FIELD: SYNC_ERROR,
            AMAZON_REQUEST_TIMESTAMP_FIELD: field_utcnow(),
            AMAZON_MESSAGE_CODE_FIELD: type(ex).__name__,
            AMAZON_RESULT_DESCRIPTION_FIELD: ex.message
        }
        records.write(sync_status)

    @staticmethod
    def update_sync_new_empty_value(records):
        sync_status = {
            SYNC_STATUS_FIELD: SYNC_SUCCESS,
            AMAZON_REQUEST_TIMESTAMP_FIELD: field_utcnow(),
            AMAZON_MESSAGE_CODE_FIELD: 'Empty Value',
            AMAZON_RESULT_DESCRIPTION_FIELD: 'Skip sync with empty value.'
        }
        records.write(sync_status)

    @staticmethod
    def update_record(record, sync_status):
        values = dict(sync_status)
        check_count = record[SYNC_CHECK_STATUS_COUNT_FILED]
        values[SYNC_CHECK_STATUS_COUNT_FILED] = check_count + 1
        record.write(values)

    def update_message_code(self, record, message_code):
        sync_status = {AMAZON_MESSAGE_CODE_FIELD: message_code}
        self.update_record(record, sync_status)

    def update_mws_exception(self, record, ex):
        sync_status = {
            AMAZON_MESSAGE_CODE_FIELD: type(ex).__name__,
            AMAZON_RESULT_DESCRIPTION_FIELD: ex.message,
        }
        self.update_record(record, sync_status)

    def archive_old(self):
        _logger.debug("Enter ProductSyncAccess archive_old()")
        now = datetime.utcnow()
        archive_date = now - timedelta(days=_ARCHIVE_DAYS)
        archive_date_str = archive_date.strftime(DATETIME_FORMAT)
        archive_records = self._table.search([
            (PRODUCT_CREATE_DATE_FIELD, '<', archive_date_str),
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
        _logger.debug("Archived {} timeout amazon sync records".format(
            count
        ))

    def cleanup(self):
        _logger.debug("Enter ProductSyncAccess cleanup()")
        now = datetime.utcnow()
        unlink_date = now - timedelta(days=_UNLINK_DAYS)
        unlink_date_str = unlink_date.strftime(DATETIME_FORMAT)
        unlink_records = self._table.search([
            (PRODUCT_CREATE_DATE_FIELD, '<', unlink_date_str)
        ])
        count = len(unlink_records)
        if unlink_records:
            unlink_records.unlink()

        log_template = "Cleaned {} ancient amazon sync records."
        _logger.debug(log_template.format(count))
