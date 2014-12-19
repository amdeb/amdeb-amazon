# -*- coding: utf-8 -*-

import cPickle
import logging
_logger = logging.getLogger(__name__)

from ..shared.model_names import (
    MODEL_NAME_FIELD,
    RECORD_ID_FIELD,
    PRODUCT_DEFAULT_CODE_FIELD,
    SYNC_STATUS_FIELD,
    SYNC_DATA_FIELD,
    AMAZON_MESSAGE_CODE_FIELD,
    AMAZON_REQUEST_TIMESTAMP_FIELD,
    AMAZON_SUBMISSION_ID_FIELD,
)
from ..shared.sync_status import SYNC_PENDING
from .product_sync_access import ProductSyncAccess
from ..shared.utility import field_utcnow


class ProductSyncNew(object):
    """
    This class processes new sync operations
    To match a request with response result, we use
    the sync table record id as the message id
    """
    def __init__(self, env, mws):
        self._env = env
        self._mws = mws
        self._product_sync = ProductSyncAccess(env)

    def _convert_sync(self, update):
        sync_value = {}
        sync_data = cPickle.loads(update[SYNC_DATA_FIELD])
        # ToDo: the conversion should be done in a separate module
        if 'name' in sync_data:
            sync_value['ID'] = update.id
            sync_value['Title'] = sync_data['name']
            product = self._env[update[MODEL_NAME_FIELD]].browse(
                update[RECORD_ID_FIELD])
            sync_value['SKU'] = product[PRODUCT_DEFAULT_CODE_FIELD]

        return sync_value

    def _convert_updates(self, sync_updates):
        sync_values = []
        for update in sync_updates:
            sync_value = self._convert_updates(update)
            if sync_value:
                sync_values.append(sync_value)
        return sync_values

    def _call_updates(self, sync_updates, sync_values):
        _logger.debug("about to call MWS send for product updates.")
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
        sync_updates.write(sync_result)

    def _sync_update(self):
        sync_updates = self._product_sync.get_updates()
        sync_values = self._convert_updates(sync_updates)
        if sync_values:
            self._call_updates(sync_updates, sync_values)

    def synchronize(self):
        _logger.debug("about to sync new product operations")
        self._sync_update()

        # all new syncs should exist in product table
        # because this is in the same transaction as the
        # transformer. There is no need to check existence.
