# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from ..shared.model_names import (
    PRODUCT_TEMPLATE_TABLE,
    PRODUCT_VARIANT_COUNT_FIELD,
    PRODUCT_VARIANT_IDS_FIELD,

    PRODUCT_PRODUCT_TABLE,
    MODEL_NAME_FIELD,
    RECORD_ID_FIELD,
    TEMPLATE_ID_FIELD,
    AMAZON_PRODUCT_SYNC_TABLE,
    SYNC_STATUS_FIELD,
    SYNC_TYPE_FIELD,
    AMAZON_MESSAGE_CODE_FIELD,
    AMAZON_SUBMISSION_ID_FIELD,
    AMAZON_RESULT_DESCRIPTION_FIELD,
    AMAZON_CREATION_SUCCESS_FIELD,
    AMAZON_SYNC_ACTIVE_FIELD,
    PRODUCT_PRICE_FIELD,
    PRODUCT_AVAILABLE_QUANTITY_FIELD,
)
from ..shared.sync_status import (
    SYNC_PENDING,
    SYNC_SUCCESS,
    SYNC_ERROR,
    AMAZON_PROCESS_DONE_STATUS,
)
from ..shared.sync_operation_types import (
    SYNC_CREATE,
)

from .product_sync_creation import ProductSyncCreation


class ProductSyncCompleted(object):
    """
    This class processes completed sync operations
    Instead of processing immediately after status checking,
    reading them from table makes the code more reliable
    """
    def __init__(self, env, mws):
        self._env = env
        self._mws = mws
        self._amazon_sync_table = env[AMAZON_PRODUCT_SYNC_TABLE]
        self._sync_creation = ProductSyncCreation(env)
        self._product_template = env[PRODUCT_TEMPLATE_TABLE]
        self._product_product = env[PRODUCT_PRODUCT_TABLE]
        self._completed_set = None

    def _get_completed(self):
        _logger.debug("get completed sync operations")
        search_domain = [
            (SYNC_STATUS_FIELD, '=', SYNC_PENDING),
            (AMAZON_MESSAGE_CODE_FIELD, '=', AMAZON_PROCESS_DONE_STATUS)
        ]
        self._completed_set = self._amazon_sync_table.search(search_domain)

    def _get_submission_ids(self):
        submission_ids = set()
        for pending in self._completed_set:
            submission_id = pending[AMAZON_SUBMISSION_ID_FIELD]
            submission_ids.add(submission_id)
        log_template = "get {} submission ids for completed sync operations."
        _logger.debug(log_template.format(len(submission_ids)))
        return submission_ids

    def _add_price_sync(self, record, completed):
        price = record[PRODUCT_PRICE_FIELD]
        self._sync_creation.insert_price(completed, price)

    def _add_inventory_sync(self, record, completed):
        inventory = record[PRODUCT_AVAILABLE_QUANTITY_FIELD]
        self._sync_creation.insert_inventory(completed, inventory)

    def _add_success_syncs(self, record, completed):
        self._add_price_sync(record, completed)
        self._add_inventory_sync(record, completed)
        self._sync_creation.insert_image(completed)

    def _write_creation_success(self, completed):
        model_name = completed[MODEL_NAME_FIELD]
        record_id = completed[RECORD_ID_FIELD]
        _logger.debug("write creation success for {0}, {1}".format(
            model_name, record_id
        ))
        record = self._env[model_name].browse(record_id)
        record[AMAZON_CREATION_SUCCESS_FIELD] = True
        sync_active = record[AMAZON_SYNC_ACTIVE_FIELD]
        if sync_active:
            self._add_success_syncs(record, completed)

    def _process_creation_success(self):
        for completed in self._completed_set:
            # for warning and success, set success flag
            is_success = completed[SYNC_STATUS_FIELD] != SYNC_ERROR
            is_sync_create = completed[SYNC_TYPE_FIELD] == SYNC_CREATE
            if is_sync_create and is_success:
                self._write_creation_success(completed)

    @staticmethod
    def _write_result(completed, sync_result):
        result = {}
        if sync_result:
            result[SYNC_STATUS_FIELD] = sync_result[0]
            result[AMAZON_MESSAGE_CODE_FIELD] = sync_result[1]
            result[AMAZON_RESULT_DESCRIPTION_FIELD] = sync_result[2]
        else:
            result[SYNC_STATUS_FIELD] = SYNC_SUCCESS

        _logger.debug("write completion result {0} for sync id {1}".format(
            sync_result, completed.id))
        completed.write(result)

    def _save_completion_results(self, completion_results):
        for completed in self._completed_set:
            submission_id = completed[AMAZON_SUBMISSION_ID_FIELD]
            # should have results for all
            completion_result = completion_results[submission_id]

            # if success, Amazon gives no result
            sync_result = completion_result.get(completed.id, None)
            self._write_result(completed, sync_result)

    def _get_completion_results(self, submission_ids):
        completion_results = {}
        for submission_id in submission_ids:
            completion_result = self._mws.get_sync_result(submission_id)
            completion_results[submission_id] = completion_result

        log_template = "get {} results for completed sync operations."
        _logger.debug(log_template.format(len(completion_results)))
        return completion_results

    def _check_template_created(self, completed):
        result = False
        template_id = completed[TEMPLATE_ID_FIELD]
        template_record = self._product_template.browse(template_id)
        if template_record:
            result = template_record[AMAZON_CREATION_SUCCESS_FIELD]
        return result

    @staticmethod
    def _get_created_variants(template_record):
        headers = []
        variants = template_record[PRODUCT_VARIANT_IDS_FIELD]
        for variant in variants:
            if variant[AMAZON_CREATION_SUCCESS_FIELD]:
                header = {
                    MODEL_NAME_FIELD: PRODUCT_PRODUCT_TABLE,
                    RECORD_ID_FIELD: variant.id,
                    TEMPLATE_ID_FIELD: template_record.id,
                }
                headers.append(header)
        return headers

    def _check_variant_created(self, completed):
        headers = []
        template_id = completed[RECORD_ID_FIELD]
        template_record = self._product_template.browse(template_id)
        # ToDo: what if template_record is not found (unlinked) ???
        if template_record[PRODUCT_VARIANT_COUNT_FIELD] > 1:
            headers = self._get_created_variants(template_record)
        return headers

    def _add_relation_sync(self, completed):
        if completed[MODEL_NAME_FIELD] == PRODUCT_PRODUCT_TABLE:
            if self._check_template_created(completed):
                self._sync_creation.insert_relation(completed)
            else:
                log_template = "Product template is not created for {}. " \
                               "Don't create relation sync"
                _logger.debug(log_template.format(
                    completed[RECORD_ID_FIELD]
                ))
        else:
            headers = self._check_variant_created(completed)
            for header in headers:
                self._sync_creation.insert_relation(header)

    def _process_creation_relations(self):
        # It is possible that a product template or variant
        # creation is failed and the relation
        # is not created for a product variant.
        # The automatic way to fix this is to create
        # relation syn for both template and variant creation sync
        for completed in self._completed_set:
            # for warning and success, set success flag
            is_success = completed[SYNC_STATUS_FIELD] != SYNC_ERROR
            is_sync_create = completed[SYNC_TYPE_FIELD] == SYNC_CREATE
            if is_sync_create and is_success:
                self._add_relation_sync(completed)

    def synchronize(self):
        self._get_completed()
        submission_ids = self._get_submission_ids()
        completion_results = self._get_completion_results(submission_ids)
        self._save_completion_results(completion_results)
        self._process_creation_success()

        # create relation sync in a separate step because we need to know the
        # creation status of both the template and the variant
        self._process_creation_relations()
