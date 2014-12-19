# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from ..shared.model_names import (
    PRODUCT_TEMPLATE_TABLE,

    PRODUCT_PRODUCT_TABLE,
    AMAZON_PRODUCT_SYNC_TABLE,
    SYNC_STATUS_FIELD,
    AMAZON_MESSAGE_CODE_FIELD,
    AMAZON_SUBMISSION_ID_FIELD,
    AMAZON_RESULT_DESCRIPTION_FIELD,
    SYNC_CHECK_STATUS_COUNT_FILED,
)
from ..shared.sync_status import (
    SYNC_PENDING,
    SYNC_SUCCESS,
    AMAZON_PROCESS_DONE_STATUS,
)

from .product_sync_access import ProductSyncAccess
from .amazon_product_access import AmazonProductAccess
from .product_creation_success import ProductCreationSuccess


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
        self._sync_creation = ProductSyncAccess(env)
        self._product_template = env[PRODUCT_TEMPLATE_TABLE]
        self._product_product = env[PRODUCT_PRODUCT_TABLE]
        self._completed_set = None

        self._amazon_product_access = AmazonProductAccess(env)
        self._creation_success = ProductCreationSuccess(env)

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

    @staticmethod
    def _write_exception(completed, ex):
        # keep its pending status, increase check count thus
        # it will be checked till it exceeds the checking threshold
        result = {
            AMAZON_RESULT_DESCRIPTION_FIELD: ex.message
        }
        check_count = completed[SYNC_CHECK_STATUS_COUNT_FILED]
        completed[SYNC_CHECK_STATUS_COUNT_FILED] = check_count + 1

        log_template = "Completed exception result {0} for sync id {1}"
        _logger.debug(log_template.format(result, completed.id))
        completed.write(result)

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
            result, completed.id))

        completed.write(result)

    def _save_completion_results(self, completion_results):
        for completed in self._completed_set:
            submission_id = completed[AMAZON_SUBMISSION_ID_FIELD]
            # should have results for all
            completion_result = completion_results[submission_id]
            if isinstance(completion_result, Exception):
                self._write_exception(completed, completion_result)
            else:
                # if success, Amazon gives no result
                sync_result = completion_result.get(completed.id, None)
                self._write_result(completed, sync_result)

    def _get_completion_results(self, submission_ids):
        completion_results = {}
        for submission_id in submission_ids:
            try:
                completion_result = self._mws.get_sync_result(submission_id)
                completion_results[submission_id] = completion_result
            except Exception as ex:
                log_template = "mws sync result for exception {0} for" \
                               " submission id {1}"
                _logger.debug(log_template.format(
                    ex.message, submission_id
                ))
                completion_results[submission_id] = ex

        log_template = "get {} results for completed sync operations."
        _logger.debug(log_template.format(len(completion_results)))
        return completion_results

    def synchronize(self):
        """
        Process completed sync requests
        :return: True if new sync record is added for create sync
        """
        is_new_sync_added = False
        self._get_completed()
        submission_ids = self._get_submission_ids()
        if submission_ids:
            completion_results = self._get_completion_results(submission_ids)
            self._save_completion_results(completion_results)

            # create relation sync in a separate step
            # because we need to know the
            # creation status of both the template and the variant
            is_new_sync_added = self._creation_success.process(
                self._completed_set)

        return is_new_sync_added
