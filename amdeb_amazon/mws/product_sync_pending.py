# -*- coding: utf-8 -*-

from ..shared.model_names import (
    AMAZON_PRODUCT_SYNC_TABLE,
    SYNC_STATUS_FIELD,
    # SYNC_TYPE_FIELD,
    AMAZON_MESSAGE_CODE_FIELD,
    AMAZON_SUBMISSION_ID_FIELD,
    AMAZON_RESULT_DESCRIPTION_FIELD,
    SYNC_CHECK_STATUS_COUNT_FILED,
)
from ..shared.sync_status import (
    SYNC_PENDING,
    SYNC_SUCCESS,
    # SYNC_WARNING,
    # SYNC_ERROR,
    AMAZON_PROCESS_DONE_STATUS,
)


class ProductSyncPending(object):
    """ This class processes pending syncs"""

    def __init__(self, env, mws):
        self._env = env
        self._mws = mws
        self._amazon_sync = self._env[AMAZON_PRODUCT_SYNC_TABLE]

    def _get_pending(self):
        search_domain = [
            (SYNC_STATUS_FIELD, '=', SYNC_PENDING),
        ]
        self._pending_set = self._amazon_sync.search(
            search_domain,
            order="id asc")

    def _get_submission_ids(self):
        # we use list to keep the order
        self._submission_ids = []
        for pending in self._pending_set:
            submission_id = pending[AMAZON_SUBMISSION_ID_FIELD]
            if submission_id not in self._submission_ids:
                self._submission_ids.append(submission_id)

    @staticmethod
    def _write_result(pending, sync_result):
        result = {}
        if sync_result:
            result[SYNC_STATUS_FIELD] = sync_result[0]
            result[AMAZON_MESSAGE_CODE_FIELD] = sync_result[1]
            result[AMAZON_RESULT_DESCRIPTION_FIELD] = sync_result[2]
        else:
            result[SYNC_STATUS_FIELD] = SYNC_SUCCESS

        pending.write(result)

    def _update_result(self, submission_id, sync_status):
        for pending in self._pending_set:
            if pending[AMAZON_SUBMISSION_ID_FIELD] == submission_id:
                sync_result = sync_status.get(pending.ids[0], None)
                self._write_result(pending, sync_result)

    @staticmethod
    def _write_status(pending, sync_status):
        result = {}
        check_count = pending[SYNC_CHECK_STATUS_COUNT_FILED]
        result[SYNC_CHECK_STATUS_COUNT_FILED] = check_count + 1
        result[SYNC_STATUS_FIELD] = sync_status
        pending.write(result)

    def _update_status(self, submission_status):
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

    def _check_status(self):
        submission_status = self._mws.check_sync_status(self._submission_ids)
        done_submissions = self._update_status(submission_status)
        for submission_id in done_submissions:
            sync_result = self._mws.get_sync_result(submission_id)
            self._update_result(submission_id, sync_result)

    def synchronize(self):
        #  update product table for successful creation
        # self._cleanup()

        self._get_pending()
        self._get_submission_ids()
        self._check_status()

        # self._archive_old()
