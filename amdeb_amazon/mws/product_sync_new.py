# -*- coding: utf-8 -*-

import cPickle
import logging
_logger = logging.getLogger(__name__)

from ..shared.model_names import (
    MODEL_NAME_FIELD,
    RECORD_ID_FIELD,
    AMAZON_PRODUCT_SYNC_TABLE,
    SYNC_STATUS_FIELD,
    SYNC_TYPE_FIELD,
    AMAZON_MESSAGE_CODE_FIELD,
    AMAZON_REQUEST_TIMESTAMP_FIELD,
    AMAZON_SUBMISSION_ID_FIELD,
)
from ..shared.sync_operation_types import (
    SYNC_UPDATE,
)
from ..shared.sync_status import (
    SYNC_NEW,
    SYNC_PENDING,
)


class ProductSyncNew(object):
    """
    This class processes new sync operations
    To match a request with response result, we use
    the sync table record id as the message id
    """
    def __init__(self, env, mws):
        self._env = env
        self._mws = mws
        self._amazon_sync = self._env[AMAZON_PRODUCT_SYNC_TABLE]

    def _get_updates(self):
        search_domain = [
            (SYNC_STATUS_FIELD, '=', SYNC_NEW),
            (SYNC_TYPE_FIELD, '=', SYNC_UPDATE)
        ]
        new_updates = self._amazon_sync.search(search_domain)
        _logger.debug("Found {} new product updates.".format(
            len(new_updates)
        ))
        return new_updates

    def _convert_updates(self, sync_updates):
        sync_values = []
        for update in sync_updates:
            sync_data = cPickle.loads(update.sync_data)
            # ToDo: the conversion should be done in a separate module
            if 'name' in sync_data:
                sync_value = {'ID': update.id, 'Title': sync_data['name']}
                product = self._env[update[MODEL_NAME_FIELD]].browse(
                    update[RECORD_ID_FIELD])
                sync_value['SKU'] = product.default_code
                sync_values.append(sync_value)
        return sync_values

    def _call_updates(self, sync_updates, sync_values):
        _logger.debug("about to call MWS send for product updates.")
        submission_id, submission_time, submission_status = self._mws.send(
            sync_values)

        sync_result = {
            SYNC_STATUS_FIELD: SYNC_PENDING,
            AMAZON_SUBMISSION_ID_FIELD: submission_id,
            AMAZON_REQUEST_TIMESTAMP_FIELD: submission_time,
            AMAZON_MESSAGE_CODE_FIELD: submission_status,
        }
        sync_updates.write(sync_result)

    def _sync_update(self):
        sync_updates = self._get_updates()
        sync_values = self._convert_updates(sync_updates)
        if sync_values:
            self._call_updates(sync_updates, sync_values)

    def synchronize(self):
        _logger.debug("about to sync new product operations")
        self._sync_update()
