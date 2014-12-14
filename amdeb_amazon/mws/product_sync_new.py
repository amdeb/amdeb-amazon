# -*- coding: utf-8 -*-

import cPickle
import logging
_logger = logging.getLogger(__name__)

from ..shared.model_names import (
    # PRODUCT_TEMPLATE,
    # PRODUCT_PRODUCT,
    AMAZON_PRODUCT_SYNC_TABLE,
    SYNC_STATUS_FIELD,
    SYNC_TYPE_FIELD,
    AMAZON_MESSAGE_CODE_FIELD,
    AMAZON_REQUEST_TIMESTAMP_FIELD,
    AMAZON_SUBMISSION_ID_FIELD,
)
from ..shared.sync_operation_types import (
    # SYNC_CREATE,
    SYNC_UPDATE,
    # SYNC_DELETE,
    # SYNC_PRICE,
    # SYNC_INVENTORY,
    # SYNC_IMAGE,
    # SYNC_DEACTIVATE,
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
        _logger.debug("get product updates")
        search_domain = [
            (SYNC_STATUS_FIELD, '=', SYNC_NEW),
            (SYNC_TYPE_FIELD, '=', SYNC_UPDATE)
        ]
        self._updates = self._amazon_sync.search(search_domain)

    def _convert_updates(self):
        _logger.debug("convert product updates to sync operations")
        sync_values = []
        for update in self._updates:
            sync_data = cPickle.loads(update.sync_data)
            if 'name' in sync_data:
                sync_value = {'ID': update.ids[0], 'Title': sync_data['name']}
                product = self._env[update.model_name].browse(
                    update.record_id)
                sync_value['SKU'] = product.default_code
                sync_values.append(sync_value)

        return sync_values

    def _call_updates(self, sync_values):
        _logger.debug("about to call MWS send for product updates.")
        feed_id, feed_time, feed_status = self._mws.send(sync_values)
        sync_values = {
            SYNC_STATUS_FIELD: SYNC_PENDING,
            AMAZON_SUBMISSION_ID_FIELD: feed_id,
            AMAZON_REQUEST_TIMESTAMP_FIELD: feed_time,
            AMAZON_MESSAGE_CODE_FIELD: feed_status,
        }
        self._updates.write(sync_values)

    def _sync_update(self):
        _logger.debug("about to sync product updates")
        self._get_updates()
        sync_values = self._convert_updates()
        if sync_values:
            self._call_updates(sync_values)

    def synchronize(self):
        self._sync_update()
