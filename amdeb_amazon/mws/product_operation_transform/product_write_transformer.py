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
from ...models_access import ProductOperationAccess
from .product_create_transformer import ProductCreateTransformer

_logger = logging.getLogger(__name__)


class ProductWriteTransformer(object):
    def __init__(self, env):
        self._env = env
        self._product_sync = ProductSyncAccess(env)
        self._amazon_product = AmazonProductAccess(env)
        self._odoo_product = OdooProductAccess(env)

    def _get_creation_status(self, amazon_product):
        waiting_flag = False
        error_flag = False
        if self._amazon_product.is_waiting(amazon_product):
            waiting_flag = True
        elif self._amazon_product.is_error(amazon_product):
            error_flag = True

        return waiting_flag, error_flag

    def _insert_sync_operation(self, operation, insert_method,
                               write_field_names=None):
        amazon_product = self._amazon_product.get_by_head(operation)
        if amazon_product:
            waiting_flag, error_flag = self._get_creation_status(
                amazon_product)
            if write_field_names:
                insert_method(
                    operation,
                    write_field_names=write_field_names,
                    waiting_flag=waiting_flag,
                    error_flag=error_flag)
            else:
                insert_method(
                    operation,
                    waiting_flag=waiting_flag,
                    error_flag=error_flag)
        else:
            # the only normal but rare case where there is no amazon
            # product record -- users may update
            # sync active field several times and the current one is False
            # it should be an error in other cases.
            _logger.debug("No amazon product record, not insert a new "
                          "record in product sync table.")

    def _add_sync_price(self, operation):
        variants = self._amazon_product.get_variants(
            operation[RECORD_ID_FIELD])
        if variants:
            # because we always create the template with a variant,
            # we are sure a multi-variant template has at least one
            # variant record
            for variant in variants:
                self._insert_sync_operation(
                    variant, self._product_sync.insert_price)
        else:
            self._insert_sync_operation(
                operation, self._product_sync.insert_price)

    def _transform_price(self, operation, values):
        # we don't handle the extra price change in attribute line
        # List price is only stored in template, however,
        # it can be changed in template and variant and
        # both generate write operations.
        if PRODUCT_LIST_PRICE_FIELD in values:
            values.pop(PRODUCT_LIST_PRICE_FIELD)
            if ProductOperationAccess.is_product_template(operation):
                self._add_sync_price(operation)
            else:
                _logger.debug('Skip variant {} list_price write.'.format(
                    operation[RECORD_ID_FIELD]))

    def _transform_inventory(self, operation, values):
        # the inventory is only stored in single-variant template
        # or non-partial variant, thus the operation has the
        # right product SKU
        if PRODUCT_VIRTUAL_AVAILABLE_FIELD in values:
            values.pop(PRODUCT_VIRTUAL_AVAILABLE_FIELD)
            self._insert_sync_operation(
                operation, self._product_sync.insert_inventory)

    def _transform_image(self, operation, values):
        insert_flag = False
        # create image sync regardless the image_trigger value
        # only for non-partial variant or single-variant template
        if PRODUCT_AMAZON_IMAGE_TRIGGER_FIELD in values:
            values.pop(PRODUCT_AMAZON_IMAGE_TRIGGER_FIELD)
            if ProductOperationAccess.is_product_variant(operation):
                if self._odoo_product.is_partial_variant(operation):
                    _logger.debug("ignore image trigger for partial variant.")
                else:
                    insert_flag = True
            else:
                if self._odoo_product.is_multi_variant(operation):
                    _logger.debug("ignore image trigger for "
                                  "multi-variant template.")
                else:
                    insert_flag = True

        if insert_flag:
            self._insert_sync_operation(
                operation, self._product_sync.insert_image)

    def _transform_update(self, operation, write_fields):
        self._transform_price(operation, write_fields)
        self._transform_inventory(operation, write_fields)
        self._transform_image(operation, write_fields)
        if write_fields:
            if ProductOperationAccess.is_product_template(operation):
                self._product_sync.insert_update(operation, write_fields)
                self._insert_sync_operation(
                    operation,
                    self._product_sync.insert_update,
                    write_fields)
            else:
                _logger.debug("Ignore write operation for product variant.")

    def _transform_deactivate(self, operation):
        insert_flag = False
        # ignore partial variant and multi-variant template
        if ProductOperationAccess.is_product_variant(operation):
            if self._odoo_product.is_partial_variant(operation):
                _logger.debug("Skip partial variant deactivate operation.")
            else:
                insert_flag = True
        else:
            if self._odoo_product.is_multi_variant(operation):
                # template create sync is inserted by one of its variants
                log_template = "Skip deactivate operation for template {} " \
                               "that has multi-variants."
                _logger.debug(log_template.format(operation))
            else:
                insert_flag = True

        if insert_flag:
            self._insert_sync_operation(
                operation, self._product_sync.insert_deactivate)

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


        !!! Even the sync active is True, a product Amazon creation
        might be waiting or error.
        When a new product creation is waiting, all changes
        except creation are put into waiting status.
        When the creation status is error, create a sync operation and set
        its status as Error and DONE.
        """
        sync_active_value = self._odoo_product.is_sync_active(operation)
        if AMAZON_SYNC_ACTIVE_FIELD in write_fields:
            # sync active is in the write field, use the
            # latest value to create sync operation
            self._transform_sync_active(operation, sync_active_value)
        else:
            if sync_active_value:
                # we change the local copy in other methods
                values_copy = write_fields.copy()
                self._transform_update(operation, values_copy)
            else:
                _logger.debug("Product sync flag is disabled. Ignore writes.")
