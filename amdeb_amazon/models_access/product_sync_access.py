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
    FIELD_NAME_DELIMITER, PRODUCT_SKU_FIELD,
)
from ..shared.sync_status import (
    SYNC_STATUS_NEW, SYNC_STATUS_PENDING, SYNC_STATUS_ERROR,
    AMAZON_STATUS_PROCESS_DONE, SYNC_STATUS_SUCCESS,
    SYNC_STATUS_WAITING,
)
from ..shared.sync_operation_types import (
    SYNC_CREATE, SYNC_UPDATE, SYNC_DELETE, SYNC_PRICE,
    SYNC_INVENTORY, SYNC_IMAGE, SYNC_DEACTIVATE, SYNC_RELATION,
)
from ..shared.utility import field_utcnow
from .sync_head_access import SyncHeadAccess

_UNLINK_DAYS = 100
_ARCHIVE_DAYS = 5
_ARCHIVE_CHECK_COUNT = 100
_ARCHIVE_CODE = "Timeout"
_ARCHIVE_MESSAGE = "Pending more than {0} days and {1} checks".format(
    _ARCHIVE_DAYS, _ARCHIVE_CHECK_COUNT
)
_CREATION_ERROR_CODE = "Amazon Product Creation Error."
_REDUNDANT_SKIP_CODE = "Redundant Or Merged Operation."
_PRODUCT_NOT_FOUND_CODE = "Product Not Found Or Sync Disabled."

_logger = logging.getLogger(__name__)


class ProductSyncAccess(SyncHeadAccess):
    """
    Provide methods for accessing Amazon product sync table
    The sync_head is an object that defines model_name,
    record_id and template_id. It could be a product operation record
    or an Amazon sync record
    """
    def __init__(self, env):
        self._table = env[AMAZON_PRODUCT_SYNC_TABLE]

    @staticmethod
    def _log_values(values):
        log_template = "Create new sync record for Model: {0}, " \
                       "record id: {1}, sync type: {2}, " \
                       "write fields: {3}, product sku: {4}, " \
                       "waiting flag: {5}, error_flag: {6}."
        _logger.debug(log_template.format(
            values[MODEL_NAME_FIELD],
            values[RECORD_ID_FIELD],
            values[SYNC_TYPE_FIELD],
            values.get(WRITE_FIELD_NAMES_FIELD, None),
            values.get(PRODUCT_SKU_FIELD, None),
            values.get(SYNC_STATUS_FIELD, None),
            values.get(AMAZON_MESSAGE_CODE_FIELD, None),
        ))

    def _insert(self, sync_head, sync_type,
                write_field_names=None,
                product_sku=None,
                waiting_flag=None,
                error_flag=None):
        """
        Insert a new sync operation record.
        """
        values = {
            MODEL_NAME_FIELD: sync_head[MODEL_NAME_FIELD],
            RECORD_ID_FIELD: sync_head[RECORD_ID_FIELD],
            TEMPLATE_ID_FIELD: sync_head[TEMPLATE_ID_FIELD],
            SYNC_TYPE_FIELD: sync_type,
        }
        if write_field_names:
            values[WRITE_FIELD_NAMES_FIELD] = FIELD_NAME_DELIMITER.join(
                write_field_names)
        if product_sku:
            values[PRODUCT_SKU_FIELD] = product_sku
        if waiting_flag:
            values[SYNC_STATUS_FIELD] = SYNC_STATUS_WAITING
        if error_flag:
            values[SYNC_STATUS_FIELD] = SYNC_STATUS_ERROR
            values[AMAZON_MESSAGE_CODE_FIELD] = _CREATION_ERROR_CODE
        ProductSyncAccess._log_values(values)

        # there might be an existing sync for the same product and sync type
        # because there are existing waiting syncs or some waiting
        # syncs change to New  -- it is rare but exists.
        # However, check existing sync here for every new sync is
        # expensive. Duplicated write syncs are tolerated.
        # We know that there is no duplicated create/delete syncs.
        self._table.create(values)

    def insert_create_if_new(self, sync_head):
        # this is called when a non-partial variant adds
        # its template
        is_inserted = False
        search_domain = [
            (MODEL_NAME_FIELD, '=', sync_head[MODEL_NAME_FIELD]),
            (RECORD_ID_FIELD, '=', sync_head[RECORD_ID_FIELD]),
            (SYNC_STATUS_FIELD, '=', SYNC_STATUS_NEW),
            (SYNC_TYPE_FIELD, '=', SYNC_CREATE),
        ]
        records = self._table.search(search_domain)
        if records:
            log_template = "Create sync exists for template. Skip it."
            _logger.debug(log_template.format(sync_head))
        else:
            self.insert_create(sync_head)
            is_inserted = True

        return is_inserted

    def insert_create(self, sync_head):
        self._insert(sync_head, SYNC_CREATE)

    def insert_price(self, sync_head, waiting_flag=None, error_flag=None):
        self._insert(sync_head, SYNC_PRICE,
                     waiting_flag=waiting_flag,
                     error_flag=error_flag)

    def insert_inventory(self, sync_head, waiting_flag=None, error_flag=None):
        self._insert(sync_head, SYNC_INVENTORY,
                     waiting_flag=waiting_flag,
                     error_flag=error_flag)

    def insert_image(self, sync_head, waiting_flag=None, error_flag=None):
        self._insert(sync_head, SYNC_IMAGE,
                     waiting_flag=waiting_flag,
                     error_flag=error_flag)

    def insert_update(self, sync_head, write_field_names,
                      waiting_flag=None, error_flag=None):
        self._insert(sync_head, SYNC_UPDATE,
                     write_field_names=write_field_names,
                     waiting_flag=waiting_flag,
                     error_flag=error_flag)

    def insert_deactivate(self, sync_head,
                          waiting_flag=None, error_flag=None):
        self._insert(sync_head, SYNC_DEACTIVATE,
                     waiting_flag=waiting_flag,
                     error_flag=error_flag)

    def insert_relation(self, sync_head):
        """
        Create sync relation for a product variant
        """
        self._insert(sync_head, SYNC_RELATION)

    def insert_delete(self, amazon_product):
        """
        Insert a delete sync for an amazon product object that
        has a SKU field used by Amazon API
        """
        self._insert(amazon_product, SYNC_DELETE,
                     product_sku=amazon_product[PRODUCT_SKU_FIELD])

    def _get_new_syncs(self, sync_type):
        search_domain = [
            (SYNC_STATUS_FIELD, '=', SYNC_STATUS_NEW),
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

    def get_new_images(self):
        return self._get_new_syncs(SYNC_IMAGE)

    def get_pending(self):
        # get pending in the ascending id order to
        # process the newest sync first.
        search_domain = [(SYNC_STATUS_FIELD, '=', SYNC_STATUS_PENDING)]
        return self._table.search(search_domain, order="id asc")

    def get_done(self):
        search_domain = [
            (SYNC_STATUS_FIELD, '=', SYNC_STATUS_PENDING),
            (AMAZON_MESSAGE_CODE_FIELD, '=', AMAZON_STATUS_PROCESS_DONE)
        ]
        return self._table.search(search_domain)

    @staticmethod
    def update_sync_status(records, sync_status):
        records.write(sync_status)

    @staticmethod
    def set_sync_success_code(records, message_code):
        sync_status = {
            SYNC_STATUS_FIELD: SYNC_STATUS_SUCCESS,
            AMAZON_REQUEST_TIMESTAMP_FIELD: field_utcnow(),
            AMAZON_MESSAGE_CODE_FIELD: message_code
        }
        ProductSyncAccess.update_sync_status(records, sync_status)

    @staticmethod
    def set_sync_redundant(records):
        ProductSyncAccess.set_sync_success_code(
            records, _REDUNDANT_SKIP_CODE)

    @staticmethod
    def set_sync_no_product(records):
        ProductSyncAccess.set_sync_success_code(
            records, _PRODUCT_NOT_FOUND_CODE)

    def find_set_redundant(self, sync_op):
        model_name = sync_op[MODEL_NAME_FIELD]
        record_id = sync_op[RECORD_ID_FIELD]
        sync_type = sync_op[SYNC_TYPE_FIELD]
        log_template = "About to set redundant syncs for {0}:{1}, " \
                       "Sync type: {2}."
        _logger.debug(log_template.format(model_name, record_id, sync_type))
        search_domain = [
            (MODEL_NAME_FIELD, '=', model_name),
            (RECORD_ID_FIELD, '=', record_id),
            ('id', '!=', sync_op.id),
            (SYNC_STATUS_FIELD, 'in', [SYNC_STATUS_NEW, SYNC_STATUS_WAITING])
        ]
        records = self._table.search(search_domain)
        if records:
            log_template = "Found {0} redundant syncs, ids: {1}."
            _logger.debug(log_template.format(len(records), record_id.ids))
            ProductSyncAccess.set_sync_redundant(records)
        else:
            _logger.debug("Found no redundant sync operations.")

    @staticmethod
    def update_sync_new_exception(records, ex):
        sync_status = {
            SYNC_STATUS_FIELD: SYNC_STATUS_ERROR,
            AMAZON_REQUEST_TIMESTAMP_FIELD: field_utcnow(),
            AMAZON_MESSAGE_CODE_FIELD: type(ex).__name__,
            AMAZON_RESULT_DESCRIPTION_FIELD: ex.message
        }
        records.write(sync_status)

    @staticmethod
    def update_sync_new_empty_value(records):
        sync_status = {
            SYNC_STATUS_FIELD: SYNC_STATUS_SUCCESS,
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

    @staticmethod
    def update_message_code(record, message_code):
        sync_status = {AMAZON_MESSAGE_CODE_FIELD: message_code}
        ProductSyncAccess.update_record(record, sync_status)

    @staticmethod
    def update_mws_exception(record, ex):
        sync_status = {
            AMAZON_MESSAGE_CODE_FIELD: type(ex).__name__,
            AMAZON_RESULT_DESCRIPTION_FIELD: ex.message,
        }
        ProductSyncAccess.update_record(record, sync_status)

    def update_waiting_to_new(self, sync_op):
        search_domain = [
            (MODEL_NAME_FIELD, '=', sync_op[MODEL_NAME_FIELD]),
            (RECORD_ID_FIELD, '=', sync_op[RECORD_ID_FIELD]),
            (SYNC_STATUS_FIELD, '=', SYNC_STATUS_WAITING),
        ]
        records = self._table.search(search_domain)
        if records:
            records.write({SYNC_STATUS_FIELD: SYNC_STATUS_NEW})
            log_template = "Change {} waiting syncs to new status."
            _logger.debug(log_template.format(len(records)))

    def archive_old(self):
        _logger.debug("Enter ProductSyncAccess archive_old()")
        now = datetime.utcnow()
        archive_date = now - timedelta(days=_ARCHIVE_DAYS)
        archive_date_str = archive_date.strftime(DATETIME_FORMAT)
        archive_records = self._table.search([
            (PRODUCT_CREATE_DATE_FIELD, '<', archive_date_str),
            (SYNC_STATUS_FIELD, '=', SYNC_STATUS_PENDING),
            (SYNC_CHECK_STATUS_COUNT_FILED, '>=', _ARCHIVE_CHECK_COUNT)
        ])
        if archive_records:
            archive_status = {
                SYNC_STATUS_FIELD: SYNC_STATUS_ERROR,
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
