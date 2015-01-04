# -*- coding: utf-8 -*-

import logging

from ...shared.model_names import (
    SYNC_STATUS_FIELD, AMAZON_MESSAGE_CODE_FIELD,
    AMAZON_REQUEST_TIMESTAMP_FIELD, AMAZON_SUBMISSION_ID_FIELD,
)
from ...shared.sync_status import SYNC_PENDING
from ...models_access import ProductSyncAccess

from ..product_sync_transform import BaseTransformer
from ..product_sync_transform import UpdateTransformer
from ..product_sync_transform import PriceTransformer
from ..product_sync_transform import InventoryTransformer

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
        self._sync_types = [
            (self._product_sync.get_new_updates,
             UpdateTransformer,
             self._mws.send_product),
            (self._product_sync.get_new_prices,
             PriceTransformer,
             self._mws.send_price),
            (self._product_sync.get_new_inventories,
             InventoryTransformer,
             self._mws.send_inventory),
            (self._product_sync.get_new_imagines,
             BaseTransformer,
             self._mws.send_image),
        ]

    @staticmethod
    def _convert_results(results):
        sync_result = {
            SYNC_STATUS_FIELD: SYNC_PENDING,
            AMAZON_SUBMISSION_ID_FIELD: results[0],
            AMAZON_REQUEST_TIMESTAMP_FIELD: results[1],
            AMAZON_MESSAGE_CODE_FIELD: results[2],
        }
        return sync_result

    def _mws_send(self, mws_send, syncs, sync_values):
        _logger.debug("about to call MWS send() for product updates.")
        # set to pending thus we keep calling send
        # even there is an exception threw
        try:
            results = mws_send(sync_values)
            sync_result = self._convert_results(results)
            self._product_sync.update_sync_new_status(syncs, sync_result)
        except Exception as ex:
            _logger.exception("mws send() threw exception.")
            self._product_sync.update_sync_new_exception(syncs, ex)

    def synchronize(self):
        _logger.debug("Enter ProductSyncNew synchronize().")
        # all new syncs should exist in product table
        # because this is in the same transaction as the
        # transformer. There is no need to check existence.
        for sync_type in self._sync_types:
            sync_ops = sync_type[0]()
            if sync_ops:
                transformer = sync_type[1](self._env)
                valid_syncs, sync_values = transformer.transform(sync_ops)
                self._mws_send(sync_type[2], valid_syncs, sync_values)
