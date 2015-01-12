# -*- coding: utf-8 -*-

import logging

from ...shared.model_names import AMAZON_SUBMISSION_ID_FIELD
from ...models_access import ProductSyncAccess

_logger = logging.getLogger(__name__)


class ProductSyncPending(object):
    """
    This class processes pending syncs ordered by ascending record ids
    """
    def __init__(self, env, mws):
        self._product_sync = ProductSyncAccess(env)
        self._mws = mws
        self._pending_set = None

    def _get_submission_ids(self):
        _logger.debug("get submission ids")
        # we use list to keep the order because we want to query
        # old submissions first
        submission_ids = []
        for pending in self._pending_set:
            submission_id = pending[AMAZON_SUBMISSION_ID_FIELD]
            if submission_id not in submission_ids:
                submission_ids.append(submission_id)
        return submission_ids

    def _update_status(self, submission_statuses):
        """
        the result may be incomplete due to mws error.
        """
        log_template = "updating {} pending sync statuses"
        _logger.debug(log_template.format(len(submission_statuses)))

        for pending in self._pending_set:
            submission_id = pending[AMAZON_SUBMISSION_ID_FIELD]
            message_code = submission_statuses.get(submission_id, None)
            if message_code:
                ProductSyncAccess.update_message_code(pending, message_code)

    def _check_status(self, submission_ids):
        log_template = "Checking sync status for {} submissions."
        _logger.debug(log_template.format(len(submission_ids)))

        submission_statuses = self._mws.check_sync_status(submission_ids)
        if submission_statuses:
            self._update_status(submission_statuses)

    def synchronize(self):
        """
        The mws call swallows exception to return any results it has.
        """
        _logger.debug("Enter ProductSyncPending synchronize()")
        try:
            self._pending_set = self._product_sync.search_pending()
            log_template = "Got {} pending syncs."
            _logger.debug(log_template.format(len(self._pending_set)))

            if self._pending_set:
                submission_ids = self._get_submission_ids()
                log_template = "Got {0} submission ids: {1}"
                _logger.debug(log_template.format(
                    len(submission_ids), submission_ids))
                self._check_status(submission_ids)
        except:
            _logger.exception("Exception in ProductSyncPending synchronize().")
