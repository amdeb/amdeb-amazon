# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from ..shared.model_names import (
    AMAZON_PRODUCT_SYNC_TABLE,
    SYNC_STATUS_FIELD,
    AMAZON_MESSAGE_CODE_FIELD,
    AMAZON_SUBMISSION_ID_FIELD,
    SYNC_CHECK_STATUS_COUNT_FILED,
)
from ..shared.sync_status import (
    SYNC_PENDING,
)


class ProductSyncPending(object):
    """
    This class processes pending syncs ordered by ascending record ids
    """

    def __init__(self, env, mws):
        self._env = env
        self._mws = mws
        self._amazon_sync_table = self._env[AMAZON_PRODUCT_SYNC_TABLE]
        self._pending_set = None

    def _get_pending(self):
        _logger.debug("get pending syncs")
        search_domain = [
            (SYNC_STATUS_FIELD, '=', SYNC_PENDING),
        ]
        self._pending_set = self._amazon_sync_table.search(
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

    def _write_status(self, pending, sync_status):
        result = {}
        check_count = pending[SYNC_CHECK_STATUS_COUNT_FILED]
        result[SYNC_CHECK_STATUS_COUNT_FILED] = check_count + 1
        result[AMAZON_MESSAGE_CODE_FIELD] = sync_status
        pending.write(result)

    def _update_status(self, submission_statuses):
        _logger.debug("updating {} pending sync statuses".format(
            len(submission_statuses)
        ))
        for pending in self._pending_set:
            submission_id = pending[AMAZON_SUBMISSION_ID_FIELD]
            sync_status = submission_statuses[submission_id]
            self._write_status(pending, sync_status)

    def _set_exception_status(self, ex):
         for pending in self._pending_set:
            self._write_status(pending, ex.message)

    def _check_status(self, submission_ids):
        log_template = "Checking sync status for {} submissions."
        _logger.debug(log_template.format(len(submission_ids)))

        try:
            submission_statuses = self._mws.check_sync_status(submission_ids)
            self._update_status(submission_statuses)
        except Exception as ex:
            _logger.warning("mws check sync status exception: {}.".format(
                ex.message
            ))
            self._set_exception_status(ex)

    def synchronize(self):
        """
        1. get pending submissions
        2. update submission status
        """
        _logger.debug("about to check pending sync status")
        self._get_pending()
        submission_ids = self._get_submission_ids()
        if submission_ids:
            self._check_status(submission_ids)
