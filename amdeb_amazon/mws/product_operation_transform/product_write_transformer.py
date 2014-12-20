# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from ...shared.model_names import (
    AMAZON_SYNC_ACTIVE_FIELD,
    PRODUCT_PRICE_FIELD,
    PRODUCT_AVAILABLE_QUANTITY_FIELD,
    PRODUCT_AMAZON_IMAGE_TRIGGER_FIELD,
)

from ...models_access import ProductSyncAccess
from ...models_access import AmazonProductAccess


class ProductWriteTransformer(object):
    def __init__(self, env):
        self._env = env
        self._sync_creation = ProductSyncAccess(env)
        self._amazon_product_access = AmazonProductAccess(env)

    def _transform_price(self, operation, write_values):
        price = write_values.pop(PRODUCT_PRICE_FIELD, None)
        if price is not None:
            self._sync_creation.insert_price(operation, price)

    def _transform_inventory(self, operation, write_values):
        inventory = write_values.pop(PRODUCT_AVAILABLE_QUANTITY_FIELD, None)
        if inventory is not None:
            self._sync_creation.insert_inventory(operation, inventory)

    def _transform_image(self, operation, write_values):
        image_trigger = write_values.pop(
            PRODUCT_AMAZON_IMAGE_TRIGGER_FIELD, None)
        # create image sync regardless the image_trigger value
        if image_trigger is not None:
            self._sync_creation.insert_image(operation)

    def _transform_update(self, operation, write_values):
        self._transform_price(operation, write_values)
        self._transform_inventory(operation, write_values)
        self._transform_image(operation, write_values)
        if write_values:
            self._sync_creation.insert_update(operation, write_values)

    def transform(self, operation, write_values, sync_active):
        """transform a write operation to one or more sync operations
        1. If sync active changes, generate create or deactivate sync. Done
        2. If sync active or creation_success is False, ignore all changes.
        Done.
        3. If price, inventory and image change, generate
        corresponding syncs. image triggers is set to False.
        4. If any write values left, generate an update sync
        """
        sync_active_value = write_values.get(AMAZON_SYNC_ACTIVE_FIELD, None)
        is_created = self._amazon_product_access.is_created(operation)
        if sync_active_value is not None:
            if sync_active_value:
                _logger.debug("Amazon sync active changes to "
                              "True, generate a create sync.")
                self._sync_creation.insert_create(operation)
            else:
                # no need to deactivate it if not created
                if is_created:
                    _logger.debug("Amazon sync active changes to "
                                  "False, generate a deactivate sync.")
                    self._sync_creation.insert_deactivate(operation)
        else:
            if sync_active and is_created:
                self._transform_update(operation, write_values)
            else:
                _logger.debug("Product write is inactive or is not created "
                              "in Amazon. Ignore it.")
