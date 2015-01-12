# -*- coding: utf-8 -*-

import logging

from ...shared.model_names import (
    RECORD_ID_FIELD,
    AMAZON_SYNC_ACTIVE_FIELD, PRODUCT_LIST_PRICE_FIELD,
    PRODUCT_VIRTUAL_AVAILABLE_FIELD,
    PRODUCT_AMAZON_IMAGE_TRIGGER_FIELD,
)
from ...shared.sync_operation_types import (
    SYNC_UPDATE, SYNC_PRICE, SYNC_INVENTORY,
    SYNC_IMAGE, SYNC_DEACTIVATE,
)
from ...models_access import ProductSyncAccess
from ...models_access import AmazonProductAccess
from ...models_access import OdooProductAccess
from ...models_access import ProductOperationAccess
from .product_create_transformer import ProductCreateTransformer

_logger = logging.getLogger(__name__)


class ProductWriteTransformer(object):
    def __init__(self, env):
        self._env = env
        self._product_sync = ProductSyncAccess(env)
        self._amazon_product = AmazonProductAccess(env)
        self._odoo_product = OdooProductAccess(env)

        self._current_amazon_product = None

    def _get_creation_status(self, amazon_product):
        waiting_flag = False
        error_flag = False
        if self._amazon_product.is_waiting(amazon_product):
            waiting_flag = True
        elif self._amazon_product.is_error(amazon_product):
            error_flag = True

        return waiting_flag, error_flag

    def _insert_sync_operation(self, operation, sync_type,
                               write_field_names=None):

        waiting_flag, error_flag = self._get_creation_status(
            self._current_amazon_product)
        self._product_sync.insert_sync(
            operation, sync_type,
            write_field_names=write_field_names,
            waiting_flag=waiting_flag,
            error_flag=error_flag)

    def _add_sync_price(self, operation):
        variants = self._amazon_product.get_variants(
            operation[RECORD_ID_FIELD])
        if variants:
            # because we always create the template with a variant,
            # we are sure a multi-variant template has at least one
            # variant record
            for variant in variants:
                self._insert_sync_operation(variant, SYNC_PRICE)
        else:
            self._insert_sync_operation(operation, SYNC_PRICE)

    def _transform_price(self, operation, values):
        # we don't handle the extra price change in attribute line
        # List price is only stored in template, however,
        # it can be changed in template and variant and
        # both generate write operations.
        if PRODUCT_LIST_PRICE_FIELD in values:
            values.remove(PRODUCT_LIST_PRICE_FIELD)
            if ProductOperationAccess.is_product_template(operation):
                self._add_sync_price(operation)
            else:
                _logger.debug('Skip variant {} list_price write.'.format(
                    operation[RECORD_ID_FIELD]))

    def _transform_inventory(self, operation, values):
        # the inventory is only stored in single-variant template
        # or non-partial variant, no need to skip any inventory update
        if PRODUCT_VIRTUAL_AVAILABLE_FIELD in values:
            values.remove(PRODUCT_VIRTUAL_AVAILABLE_FIELD)
            self._insert_sync_operation(operation, SYNC_INVENTORY)

    def _transform_image(self, operation, values):
        # create image sync regardless the image_trigger value
        # only for non-partial variant or single-variant template
        if PRODUCT_AMAZON_IMAGE_TRIGGER_FIELD in values:
            values.remove(PRODUCT_AMAZON_IMAGE_TRIGGER_FIELD)
            if self._odoo_product.is_partial_variant_multi_template(
                    operation):
                _logger.debug("ignore image operation for a partial variant "
                              "or multi-variant template.")
            else:
                self._insert_sync_operation(operation, SYNC_IMAGE)

    def _transform_update(self, operation, write_fields):
        self._transform_price(operation, write_fields)
        self._transform_inventory(operation, write_fields)
        self._transform_image(operation, write_fields)
        if write_fields:
            if ProductOperationAccess.is_product_template(operation):
                self._insert_sync_operation(
                    operation, SYNC_UPDATE, write_fields)
            else:
                _logger.debug("Ignore write operation because it is a "
                              "product variant.")

    def _transform_deactivate(self, operation):
        if self._odoo_product.is_partial_variant_multi_template(
                operation):
            _logger.debug("ignore deactivate operation for a partial variant "
                          "or multi-variant template.")
        else:
            self._insert_sync_operation(operation, SYNC_DEACTIVATE)

    def _transform_sync_active(self, operation, sync_active_value):
        if sync_active_value:
            _logger.debug("Amazon sync active flag changes to True,"
                          "Call create transformer for create sync.")
            create_transformer = ProductCreateTransformer(self._env)
            create_transformer.transform(operation)
        else:
            if AmazonProductAccess.is_sync_enabled(
                    self._current_amazon_product):
                _logger.debug("Amazon sync active flag changes to "
                              "False, generate a deactivate sync.")
                self._transform_deactivate(operation)
            else:
                _logger.debug("Product is not created in Amazon. "
                              "Ignore deactivate sync.")

    def transform(self, operation, write_fields):
        """
        transform a write operation to one or more sync operations
        1. If sync active value changes, generate create or deactivate sync.
        2. If product sync active is False, ignore all changes.
        3. If price, inventory or image change, generate
        corresponding syncs.
        4. If there are other write values, generate an update sync.

        deactivate, price, inventory and image can happen in both a template
        and its variant(s), need to deal with them case by case.
        Update syncs are only for product template, there is no need
        to update a variant field.

        !!! sync initial status could be New (default), Waiting or Error
        a product Amazon creation might be waiting or error.
        When a new product creation is waiting, all changes
        except creation are put into waiting status.
        When the creation status is error, create a sync operation and set
        its status as Error and DONE.
        """

        self._current_amazon_product = self._amazon_product.search_by_head(
            operation)
        sync_active_value = self._odoo_product.is_sync_active(operation)
        if AMAZON_SYNC_ACTIVE_FIELD in write_fields:
            # sync active is in the write field, use the
            # latest value to create sync operation
            self._transform_sync_active(operation, sync_active_value)
        else:
            if sync_active_value:
                if AmazonProductAccess.is_sync_enabled(
                        self._current_amazon_product):
                    # we change the local copy in other methods
                    values_copy = write_fields.copy()
                    self._transform_update(operation, values_copy)
                else:
                    _logger.debug("Product is not created in Amazon. "
                                  "Ignore write operation.")
            else:
                _logger.debug("Product sync flag is disabled. Ignore writes.")
