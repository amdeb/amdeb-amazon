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
        _logger.debug("updating {} pending sync statuses".format(
            len(submission_statuses)
        ))
        for pending in self._pending_set:
            submission_id = pending[AMAZON_SUBMISSION_ID_FIELD]
            message_code = submission_statuses[submission_id]
            self._product_sync.update_message_code(pending, message_code)

    def _set_exception_status(self, ex):
        for pending in self._pending_set:
            self._product_sync.update_exception(pending, ex)

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
        _logger.debug("Enter ProductSyncPending synchronize()")
        self._pending_set = self._product_sync.get_pending()
        _logger.debug("Got {} pending syncs.".format(len(self._pending_set)))

        if self._pending_set:
            submission_ids = self._get_submission_ids()
            self._check_status(submission_ids)
