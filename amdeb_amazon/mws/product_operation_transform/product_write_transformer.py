# -*- coding: utf-8 -*-

import logging

from ...shared.model_names import (
    RECORD_ID_FIELD,
    AMAZON_SYNC_ACTIVE_FIELD, PRODUCT_LIST_PRICE_FIELD,
    PRODUCT_VIRTUAL_AVAILABLE_FIELD,
    PRODUCT_AMAZON_IMAGE_TRIGGER_FIELD,
)

from ...models_access import ProductSyncAccess
from ...models_access import AmazonProductAccess
from ...models_access import OdooProductAccess
from .product_create_transformer import ProductCreateTransformer

_logger = logging.getLogger(__name__)


class ProductWriteTransformer(object):
    def __init__(self, env):
        self._env = env
        self._product_sync = ProductSyncAccess(env)
        self._amazon_product = AmazonProductAccess(env)
        self._odoo_product = OdooProductAccess(env)

    def _add_sync_price(self, operation):
        variants = self._amazon_product.get_variants(
            operation[RECORD_ID_FIELD])
        if variants:
            for variant in variants:
                self._product_sync.insert_price(variant)
        else:
            self._product_sync.insert_price(operation)

    def _transform_price(self, operation, values):
        # we don't handle the extra price change in attribute line
        price = values.pop(PRODUCT_LIST_PRICE_FIELD, None)
        # List price is only stored in template, however,
        # it can be changed in template and variant and
        # both generate write operations.
        if price is not None:
            if OdooProductAccess.is_product_template(operation):
                self._add_sync_price(operation)
            else:
                _logger.debug('Skip variant {} list_price write.'.format(
                    operation[RECORD_ID_FIELD]))

    def _transform_inventory(self, operation, values):
        # the inventory is only stored in single-variant template
        # or non-partial variant, thus the operation has the
        # right product SKU
        inventory = values.pop(PRODUCT_VIRTUAL_AVAILABLE_FIELD, None)
        if inventory is not None:
            self._product_sync.insert_inventory(operation)

    def _transform_image(self, operation, values):
        image_trigger = values.pop(PRODUCT_AMAZON_IMAGE_TRIGGER_FIELD, None)
        insert_flag = False
        # create image sync regardless the image_trigger value
        # only for non-partial variant or single-variant template
        if image_trigger is not None:
            if OdooProductAccess.is_product_variant(operation):
                if self._odoo_product.is_partial_variant(operation):
                    _logger.debug("ignore image trigger for partial variant.")
                else:
                    insert_flag = True
            else:
                template = self._odoo_product.browse(operation)
                if self._odoo_product.has_multi_variants(template):
                    _logger.debug("ignore image trigger for "
                                  "multi-variant template.")
                else:
                    insert_flag = True

        if insert_flag:
            self._product_sync.insert_image(operation)

    def _transform_update(self, operation, write_values):
        self._transform_price(operation, write_values)
        self._transform_inventory(operation, write_values)
        self._transform_image(operation, write_values)
        if write_values:
            if OdooProductAccess.is_product_template(operation):
                self._product_sync.insert_update(operation, write_values)
            else:
                _logger.debug("Ignore write operation for product variant.")

    def _transform_deactivate(self, operation):
        # ignore partial variant and multi-variant template
        if OdooProductAccess.is_product_variant(operation):
            if self._odoo_product.is_partial_variant(operation):
                _logger.debug("Skip partial variant deactivate operation.")
            else:
                self._product_sync.insert_deactivate(operation)
        else:
            template = self._odoo_product.browse(operation)
            if self._odoo_product.has_multi_variants(template):
                # template create sync is inserted by one of its variants
                log_template = "Skip deactivate operation for template {} " \
                               "that has multi-variants."
                _logger.debug(log_template.format(operation))
            else:
                self._product_sync.insert_deactivate(operation)

    def _transform_sync_active(self, operation, sync_active_value):
        if sync_active_value:
            _logger.debug("Amazon sync active flag changes to True,"
                          "call create transformer for create sync.")
            create_transformer = ProductCreateTransformer(self._env)
            create_transformer.transform(operation)
        else:
            _logger.debug("Amazon sync active flag changes to "
                          "False, generate a deactivate sync.")
            self._transform_deactivate(operation)

    def transform(self, operation, write_values):
        """transform a write operation to one or more sync operations
        1. If sync active value changes, generate create or deactivate sync.
        2. If product sync active is False, ignore all changes.
        3. If price, inventory or image change, generate
        corresponding syncs.
        4. If there are other write values, generate an update sync
        only for product template -- there is no need to update a variant
        field.

        !!!  When a new product creation is being processed in Amazon and
        there are new updates locally, it is possible that the update sync
        fails because the product is not created in Amazon yet.
        we don't check Amazon creation status thus a mws call may fail if
        the product is not successfully created in Amazon -- the error is a
        remainder to a user that the product is not created yet
        and a manual fix is required.
        """
        sync_active_value = write_values.get(AMAZON_SYNC_ACTIVE_FIELD, None)
        if sync_active_value is not None:
            self._transform_sync_active(operation, sync_active_value)
        else:
            product_sync_active = self._odoo_product.is_sync_active(operation)
            if product_sync_active:
                # we change the local copy in other methods
                values_copy = write_values.copy()
                self._transform_update(operation, values_copy)
            else:
                _logger.debug("Product sync flag is disabled. Ignore it.")
