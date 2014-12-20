# -*- coding: utf-8 -*-

import logging

from ...shared.model_names import (
    SYNC_STATUS_FIELD, AMAZON_MESSAGE_CODE_FIELD,
    AMAZON_REQUEST_TIMESTAMP_FIELD, AMAZON_SUBMISSION_ID_FIELD,
)
from ...shared.sync_status import SYNC_PENDING
from ...models_access import ProductSyncAccess
from ...shared.utility import field_utcnow

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

    def _mws_send(self, syncs, sync_values):
        _logger.debug("about to call MWS send() for product updates.")
        sync_result = {SYNC_STATUS_FIELD: SYNC_PENDING}
        try:
            results = self._mws.send(sync_values)
            submission_id, submission_time, submission_status = (
                results[0], results[1], results[2])
            sync_result[AMAZON_SUBMISSION_ID_FIELD] = submission_id
            sync_result[AMAZON_REQUEST_TIMESTAMP_FIELD] = submission_time
            sync_result[AMAZON_MESSAGE_CODE_FIELD] = submission_status
        except Exception as ex:
            sync_result[AMAZON_REQUEST_TIMESTAMP_FIELD] = field_utcnow()
            sync_result[AMAZON_MESSAGE_CODE_FIELD] = ex.message
            _logger.warning("mws update exception message: {}".format(
                ex.message
            ))
        _logger.debug("save mws update result: {}".format(sync_result))
        syncs.write(sync_result)

    def _sync_update(self):
        sync_updates = self._product_sync.get_updates()
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
