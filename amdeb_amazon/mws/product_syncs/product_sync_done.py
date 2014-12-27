# -*- coding: utf-8 -*-

import logging

from ...shared.model_names import (
    SYNC_STATUS_FIELD, AMAZON_MESSAGE_CODE_FIELD,
    AMAZON_SUBMISSION_ID_FIELD, AMAZON_RESULT_DESCRIPTION_FIELD,
)
from ...shared.sync_status import SYNC_SUCCESS
from ...models_access import ProductSyncAccess

_logger = logging.getLogger(__name__)


class ProductSyncDone(object):
    """
    This class processes completed sync operations
    Instead of processing immediately after status checking,
    reading them from table makes the code more reliable
    """
    def __init__(self, env, mws):
        self._mws = mws
        self._product_sync = ProductSyncAccess(env)
        self._done_set = None

    def _get_submission_ids(self):
        submission_ids = set()
        for done in self._done_set:
            submission_id = done[AMAZON_SUBMISSION_ID_FIELD]
            submission_ids.add(submission_id)
        log_template = "get {} submission ids for completed sync operations."
        _logger.debug(log_template.format(len(submission_ids)))
        return submission_ids

    def _write_result(self, done, sync_result):
        result = {}
        if sync_result:
            result[SYNC_STATUS_FIELD] = sync_result[0]
            result[AMAZON_MESSAGE_CODE_FIELD] = sync_result[1]
            result[AMAZON_RESULT_DESCRIPTION_FIELD] = sync_result[2]
        else:
            result[SYNC_STATUS_FIELD] = SYNC_SUCCESS

        _logger.debug("write completion result {0} for sync id {1}".format(
            result, done.id))
        self._product_sync.update_record(done, result)

    def _save_done_results(self, completion_results):
        for done in self._done_set:
            submission_id = done[AMAZON_SUBMISSION_ID_FIELD]
            # should have results for all
            completion_result = completion_results[submission_id]
            if isinstance(completion_result, Exception):
                self._product_sync.update_mws_exception(
                    done, completion_result)
            else:
                # if success, Amazon gives no result
                sync_result = completion_result.get(done.id, None)
                self._write_result(done, sync_result)

    def _get_results(self, submission_ids):
        completion_results = {}
        for submission_id in submission_ids:
            try:
                completion_result = self._mws.get_sync_result(submission_id)
                completion_results[submission_id] = completion_result
            except Exception as ex:
                log_template = "mws sync result for exception {0} for" \
                               " submission id {1}"
                _logger.debug(log_template.format(ex.message, submission_id))
                completion_results[submission_id] = ex

        log_template = "get {} results for completed sync operations."
        _logger.debug(log_template.format(len(completion_results)))
        return completion_results

    def synchronize(self):
        """
        Process completed sync requests
        """
        _logger.debug("Enter ProductSyncDone synchronize()")
        self._done_set = self._product_sync.get_done()
        _logger.debug("Got {} done syncs.".format(len(self._done_set)))

        if self._done_set:
            submission_ids = self._get_submission_ids()
            completion_results = self._get_results(submission_ids)
            self._save_done_results(completion_results)

        return self._done_set
