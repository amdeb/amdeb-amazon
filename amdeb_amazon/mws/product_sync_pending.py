# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from ..shared.model_names import (
    AMAZON_PRODUCT_SYNC_TABLE,
    SYNC_STATUS_FIELD,
    SYNC_TYPE_FIELD,
    AMAZON_MESSAGE_CODE_FIELD,
    AMAZON_SUBMISSION_ID_FIELD,
    AMAZON_RESULT_DESCRIPTION_FIELD,
    SYNC_CHECK_STATUS_COUNT_FILED,
    AMAZON_CREATION_SUCCESS_FIELD,
)
from ..shared.sync_status import (
    SYNC_PENDING,
    SYNC_SUCCESS,
    SYNC_ERROR,
    AMAZON_PROCESS_DONE_STATUS,
)
from ..shared.sync_operation_types import SYNC_CREATE


class ProductSyncPending(object):
    """ This class processes pending syncs"""

    def __init__(self, env, mws):
        self._env = env
        self._mws = mws
        self._amazon_sync = self._env[AMAZON_PRODUCT_SYNC_TABLE]

    def _get_pending(self):
        _logger.debug("get pending syncs")
        search_domain = [
            (SYNC_STATUS_FIELD, '=', SYNC_PENDING),
        ]
        self._pending_set = self._amazon_sync.search(
            search_domain,
            order="id asc")

    def _get_submission_ids(self):
        _logger.debug("get submission ids")
        # we use list to keep the order
        submission_ids = []
        for pending in self._pending_set:
            submission_id = pending[AMAZON_SUBMISSION_ID_FIELD]
            if submission_id not in submission_ids:
                submission_ids.append(submission_id)
        return submission_ids

    def _set_creation_success(self, model_name, record_id):
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

        # for warning and success, set success flag
        create_success = (
            pending[SYNC_TYPE_FIELD] == SYNC_CREATE and
            result[SYNC_STATUS_FIELD] != SYNC_ERROR)
        if create_success:
            model_name = pending.model_name
            record_id = pending.record_id
            _logger.debug("set creation success for {0}, {1}".format(
                model_name, record_id
            ))
            self._set_creation_success(model_name, record_id)

    def _update_result(self, submission_id, sync_status):
        _logger.debug("updating completion result for {0}, {1}".format(
            submission_id, sync_status
        ))
        for pending in self._pending_set:
            if pending[AMAZON_SUBMISSION_ID_FIELD] == submission_id:
                sync_result = sync_status.get(pending.ids[0], None)
                self._write_result(pending, sync_result)

    def _write_status(self, pending, sync_status):
        result = {}
        check_count = pending[SYNC_CHECK_STATUS_COUNT_FILED]
        result[SYNC_CHECK_STATUS_COUNT_FILED] = check_count + 1
        result[AMAZON_MESSAGE_CODE_FIELD] = sync_status
        pending.write(result)

    def _update_status(self, submission_status):
        _logger.debug("updating pending sync status")
        # we use list to keep the order
        done_submissions = []
        for pending in self._pending_set:
            submission_id = pending[AMAZON_SUBMISSION_ID_FIELD]
            sync_status = submission_status[submission_id]
            self._write_status(pending, sync_status)

            if (sync_status == AMAZON_PROCESS_DONE_STATUS and
                    submission_id not in done_submissions):
                done_submissions.append(submission_id)
        return done_submissions

    def _check_status(self, submission_ids):
        _logger.debug("checking sync status for {}".format(submission_ids))

        submission_status = self._mws.check_sync_status(submission_ids)
        done_submissions = self._update_status(submission_status)
        for submission_id in done_submissions:
            sync_result = self._mws.get_sync_result(submission_id)
            self._update_result(submission_id, sync_result)

    def synchronize(self):
        _logger.debug("about to check pending sync status")
        self._get_pending()
        submission_ids = self._get_submission_ids()
        self._check_status(submission_ids)
