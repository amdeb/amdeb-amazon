# -*- coding: utf-8 -*-

import logging

from ...shared.model_names import (
    SYNC_STATUS_FIELD, AMAZON_MESSAGE_CODE_FIELD,
    AMAZON_REQUEST_TIMESTAMP_FIELD, AMAZON_SUBMISSION_ID_FIELD,
)
from ...shared.sync_status import SYNC_PENDING
from ...models_access import ProductSyncAccess

from ..product_sync_transform import UpdateTransformer

_logger = logging.getLogger(__name__)


class ProductSyncNew(object):
    """
    This class processes new sync operations.

    To match a request with response result, we use
    the sync table record id as the message id
    """
    def __init__(self, env, mws):
        self._env = env
        self._mws = mws
        self._product_sync = ProductSyncAccess(env)

    @staticmethod
    def _convert_results(results):
        sync_result = {
            SYNC_STATUS_FIELD: SYNC_PENDING,
            AMAZON_SUBMISSION_ID_FIELD: results[0],
            AMAZON_REQUEST_TIMESTAMP_FIELD: results[1],
            AMAZON_MESSAGE_CODE_FIELD: results[2],
        }
        return sync_result

    def _mws_send(self, syncs, sync_values):
        _logger.debug("about to call MWS send() for product updates.")
        # set to pending thus we keep calling send
        # even there is an exception threw
        try:
            results = self._mws.send(sync_values)
            sync_result = self._convert_results(results)
            self._product_sync.update_sync_new_status(syncs, sync_result)
        except Exception as ex:
            log_template = "mws send() threw exception: {}"
            _logger.warning(log_template.format(ex.message))
            self._product_sync.update_sync_new_exception(syncs, ex)

    def _sync_update(self):
        sync_updates = self._product_sync.get_updates()
        _logger.debug("Found {} product update operations.".format(
            len(sync_updates)
        ))
        if sync_updates:
            update_transformer = UpdateTransformer(self._env)
            sync_values = update_transformer.transform(sync_updates)
            if sync_values:
                self._mws_send(sync_updates, sync_values)

    def synchronize(self):
        _logger.debug("Enter ProductSyncNew synchronize().")
        self._sync_update()

        # all new syncs should exist in product table
        # because this is in the same transaction as the
        # transformer. There is no need to check existence.
