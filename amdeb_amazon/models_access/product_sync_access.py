# -*- coding: utf-8 -*-

import logging

from ..model_names.shared_names import (
    MODEL_NAME_FIELD, RECORD_ID_FIELD,
    TEMPLATE_ID_FIELD, PRODUCT_SKU_FIELD,
    WRITE_FIELD_NAMES_FIELD,
)
from ..model_names.product_sync import (
    AMAZON_PRODUCT_SYNC_TABLE,
    SYNC_TYPE_FIELD,
    SYNC_STATUS_FIELD,
    SYNC_CHECK_STATUS_COUNT_FILED,
    AMAZON_MESSAGE_CODE_FIELD,
    AMAZON_RESULT_DESCRIPTION_FIELD,
    AMAZON_REQUEST_TIMESTAMP_FIELD,
    SYNC_DELETE,
    SYNC_STATUS_NEW, SYNC_STATUS_PENDING,
    SYNC_STATUS_ERROR, AMAZON_STATUS_PROCESS_DONE,
    SYNC_STATUS_SUCCESS, SYNC_STATUS_WAITING,
)
from ..shared.utility import field_utcnow
from .sync_head_access import SyncHeadAccess

_CREATION_ERROR_CODE = "Amazon Product Is Not Created Or Being Created."
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

    def insert_sync(self, sync_head, sync_type,
                    write_field_names=None, product_sku=None,
                    waiting_flag=None, error_flag=None):
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
            ProductSyncAccess.save_write_field_names(
                values, write_field_names)
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

    def insert_sync_if_new(self, sync_head, sync_type):
        # this is called when a non-partial variant adds
        # its template
        is_inserted = False
        model_name = sync_head[MODEL_NAME_FIELD]
        record_id = sync_head[RECORD_ID_FIELD]
        log_template = "About to insert sync {0}:{1} with type {2}."
        _logger.debug(log_template.format(model_name, record_id, sync_type))
        search_domain = [
            (MODEL_NAME_FIELD, '=', model_name),
            (RECORD_ID_FIELD, '=', record_id),
            (SYNC_STATUS_FIELD, '=', SYNC_STATUS_NEW),
            (SYNC_TYPE_FIELD, '=', sync_type),
        ]
        records = self._table.search(search_domain)
        if records:
            _logger.debug("Sync record exists, skip insert.")
        else:
            self.insert_sync(sync_head, sync_type)
            is_inserted = True

        return is_inserted

    def insert_delete(self, amazon_product):
        """
        Insert a delete sync for an amazon product object that
        has a SKU field used by Amazon API
        """
        self.insert_sync(
            amazon_product, SYNC_DELETE,
            product_sku=amazon_product[PRODUCT_SKU_FIELD])

    def search_new_type(self, sync_type):
        search_domain = [
            (SYNC_STATUS_FIELD, '=', SYNC_STATUS_NEW),
            (SYNC_TYPE_FIELD, '=', sync_type)
        ]
        return self._table.search(search_domain)

    def search_pending(self):
        # get pending in the ascending id order to
        # process the old sync first.
        search_domain = [(SYNC_STATUS_FIELD, '=', SYNC_STATUS_PENDING)]
        return self._table.search(search_domain, order="id asc")

    def search_done(self):
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
