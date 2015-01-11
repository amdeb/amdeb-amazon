# -*- coding: utf-8 -*-

import logging

from ...shared.model_names import (
    SYNC_STATUS_FIELD, AMAZON_MESSAGE_CODE_FIELD,
    AMAZON_REQUEST_TIMESTAMP_FIELD, AMAZON_SUBMISSION_ID_FIELD,
)
from ...shared.sync_status import SYNC_STATUS_PENDING
from ...models_access import ProductSyncAccess

from ..product_sync_transform import BaseTransformer
from ..product_sync_transform import UpdateTransformer
from ..product_sync_transform import PriceTransformer
from ..product_sync_transform import InventoryTransformer
from ..product_sync_transform import CreateTransformer

_logger = logging.getLogger(__name__)


class ProductSyncNew(object):
    """
    This class processes new sync operations.
    To match a request with response result, we use
    the sync table record id as the message id
    """
    def _create_sync_types(self):
        create_sync = (self._product_sync.get_new_creates,
                       CreateTransformer, self._mws.send_product)
        update_sync = (self._product_sync.get_new_updates,
                       UpdateTransformer, self._mws.send_product)
        price_sync = (self._product_sync.get_new_prices,
                      PriceTransformer, self._mws.send_price)
        inventory_sync = (self._product_sync.get_new_inventories,
                          InventoryTransformer, self._mws.send_inventory)
        image_sync = (self._product_sync.get_new_images,
                      BaseTransformer, self._mws.send_image)

        # the order matters because delete and create override other syncs
        self._sync_types = [
            create_sync, update_sync, price_sync,
            inventory_sync, image_sync,
        ]

    def __init__(self, env, mws):
        self._env = env
        self._mws = mws
        self._product_sync = ProductSyncAccess(env)
        self._create_sync_types()

    @staticmethod
    def _convert_results(results):
        sync_result = {
            SYNC_STATUS_FIELD: SYNC_STATUS_PENDING,
            AMAZON_SUBMISSION_ID_FIELD: results[0],
            AMAZON_REQUEST_TIMESTAMP_FIELD: results[1],
            AMAZON_MESSAGE_CODE_FIELD: results[2],
        }
        return sync_result

    def _mws_send(self, mws_send, syncs, sync_values):
        log_template = "about to call MWS send() for product syncs."
        _logger.debug(log_template.format(len(sync_values)))

        try:
            results = mws_send(sync_values)
            sync_result = self._convert_results(results)
            ProductSyncAccess.update_sync_status(syncs, sync_result)
        except Exception as ex:
            # we may want to re-try for recoverable exceptions
            # for now, just report error
            _logger.exception("mws send() threw exception.")
            ProductSyncAccess.update_sync_new_exception(syncs, ex)

    def synchronize(self):
        _logger.debug("Enter ProductSyncNew synchronize().")
        # Some waiting syncs may change to new
        # need to check product existence and duplicated/override syncs
        for sync_type in self._sync_types:
            log_template = "Processing Sync with transformer {}."
            _logger.debug(log_template.format(sync_type[1].__name__))
            sync_ops = sync_type[0]()
            if sync_ops:
                log_template = "Got {} new sync operations."
                _logger.debug(log_template.format(len(sync_ops)))

                transformer = sync_type[1](self._env)
                valid_ops, sync_values = transformer.transform(sync_ops)
                if sync_values:
                    self._mws_send(sync_type[2], valid_ops, sync_values)
                else:
                    _logger.debug("Empty sync values, skipped.")
            else:
                _logger.debug("No new operations for this transformer.")
