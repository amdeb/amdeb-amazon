# -*- coding: utf-8 -*-

import logging

from ...shared.model_names import (
    AMAZON_SYNC_ACTIVE_FIELD, PRODUCT_PRICE_FIELD,
    PRODUCT_AVAILABLE_QUANTITY_FIELD,
    PRODUCT_AMAZON_IMAGE_TRIGGER_FIELD,
)

from ...models_access import ProductSyncAccess
from ...models_access import AmazonProductAccess

_logger = logging.getLogger(__name__)


class ProductWriteTransformer(object):
    def __init__(self, env):
        self._product_sync = ProductSyncAccess(env)
        self._amazon_product = AmazonProductAccess(env)

    def _transform_price(self, operation, values):
        price = values.pop(PRODUCT_PRICE_FIELD, None)
        if price is not None:
            self._product_sync.insert_price(operation, price)

    def _transform_inventory(self, operation, values):
        inventory = values.pop(PRODUCT_AVAILABLE_QUANTITY_FIELD, None)
        if inventory is not None:
            self._product_sync.insert_inventory(operation, inventory)

    def _transform_image(self, operation, values):
        image_trigger = values.pop(PRODUCT_AMAZON_IMAGE_TRIGGER_FIELD, None)
        # create image sync regardless the image_trigger value
        if image_trigger is not None:
            self._product_sync.insert_image(operation)

    def _transform_update(self, operation, write_values):
        self._transform_price(operation, write_values)
        self._transform_inventory(operation, write_values)
        self._transform_image(operation, write_values)
        if write_values:
            self._product_sync.insert_update(operation, write_values)

    def transform(self, operation, write_values, sync_active):
        """transform a write operation to one or more sync operations
        1. If sync active changes, generate create or deactivate sync. Done
        2. If sync active is False, ignore all changes.Done.
        3. If price, inventory and image change, generate
        corresponding syncs.
        4. If any write values left, generate an update sync
        !!!  we don't check is_created thus a mws call fails if
        the product is not created in Amazon -- the error is a
        remainder to a user that the product is not created yet
        and a manual fix is required.
        """
        sync_active_value = write_values.get(AMAZON_SYNC_ACTIVE_FIELD, None)
        if sync_active_value is not None:
            if sync_active_value:
                _logger.debug("Amazon sync active changes to "
                              "True, generate a create sync.")
                self._product_sync.insert_create(operation)
            else:
                _logger.debug("Amazon sync active changes to "
                              "False, generate a deactivate sync.")
                self._product_sync.insert_deactivate(operation)
        else:
            if sync_active:
                self._transform_update(operation, write_values)
            else:
                _logger.debug("Product write is inactive. Ignore it.")
