# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from ..shared.model_names import (
    MODEL_NAME_FIELD,
    RECORD_ID_FIELD,
    AMAZON_PRODUCT_SYNC_TABLE,
    SYNC_STATUS_FIELD,
    SYNC_TYPE_FIELD,
    AMAZON_MESSAGE_CODE_FIELD,
    AMAZON_SUBMISSION_ID_FIELD,
    AMAZON_RESULT_DESCRIPTION_FIELD,
    AMAZON_CREATION_SUCCESS_FIELD,
)
from ..shared.sync_status import (
    SYNC_PENDING,
    SYNC_SUCCESS,
    SYNC_ERROR,
    AMAZON_PROCESS_DONE_STATUS,
)
from ..shared.sync_operation_types import SYNC_CREATE


class ProductSyncCompleted(object):
    """
    This class processes completed sync operations
    Instead of processing immediately after status checking,
    reading them from table makes the code more reliable
    """
    def __init__(self, env, mws):
        self._env = env
        self._mws = mws
        self._amazon_sync_table = self._env[AMAZON_PRODUCT_SYNC_TABLE]
        self._completed_set = None

    def _get_completed(self):
        _logger.debug("get completed sync operations")
        search_domain = [
            (SYNC_STATUS_FIELD, '=', SYNC_PENDING),
            (AMAZON_MESSAGE_CODE_FIELD, '=', AMAZON_PROCESS_DONE_STATUS)
        ]
        self._completed_set = self._amazon_sync_table.search(search_domain)

    def _get_submission_ids(self):
        _logger.debug("get submission ids")
        submission_ids = set()
        for pending in self._completed_set:
            submission_id = pending[AMAZON_SUBMISSION_ID_FIELD]
            submission_ids.add(submission_id)
        return submission_ids

    def _check_creation_success(self, pending, result_code):
        # for warning and success, set success flag
        is_sync_create = pending[SYNC_TYPE_FIELD] == SYNC_CREATE
        is_success = result_code != SYNC_ERROR

        # ToDo: generate price, image, inventory updates
        if is_sync_create and is_success:
            model_name = pending[MODEL_NAME_FIELD]
            record_id = pending[RECORD_ID_FIELD]
            _logger.debug("set creation success for {0}, {1}".format(
                model_name, record_id
            ))
            model = self._env[model_name].browse(record_id)
            model[AMAZON_CREATION_SUCCESS_FIELD] = True

    def _write_result(self, pending, sync_result):
        result = {}
        if sync_result:
            result[SYNC_STATUS_FIELD] = sync_result[0]
            result[AMAZON_MESSAGE_CODE_FIELD] = sync_result[1]
            result[AMAZON_RESULT_DESCRIPTION_FIELD] = sync_result[2]
        else:
            result[SYNC_STATUS_FIELD] = SYNC_SUCCESS
        pending.write(result)

        return result[SYNC_STATUS_FIELD]

    def _update_completion(self, submission_id, completion_result):
        _logger.debug("updating completion result for {0}, {1}".format(
            submission_id, completion_result
        ))
        search_domain = [
            (AMAZON_SUBMISSION_ID_FIELD, '=', submission_id),
        ]
        completed_set = self._amazon_sync_table.search(search_domain)
        for pending in completed_set:
            # not found meanings success
            sync_result = completion_result.get(pending.id, None)
            result_code = self._write_result(pending, sync_result)
            self._check_creation_success(pending, result_code)

    def _process_completions(self, submission_ids):
        for submission_id in submission_ids:
            completion_result = self._mws.get_sync_result(submission_id)
            self._update_completion(submission_id, completion_result)

    def synchronize(self):
        self._get_completed()
        submission_ids = self._get_submission_ids()
        self._process_completions(submission_ids)
