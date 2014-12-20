# -*- coding: utf-8 -*-

import logging

from ...shared.model_names import (
    PRODUCT_PRODUCT_TABLE, PRODUCT_TEMPLATE_TABLE,
    MODEL_NAME_FIELD, RECORD_ID_FIELD,
    SYNC_STATUS_FIELD, SYNC_TYPE_FIELD, TEMPLATE_ID_FIELD,
    PRODUCT_PRICE_FIELD, PRODUCT_AVAILABLE_QUANTITY_FIELD,
)
from ...shared.sync_status import SYNC_WARNING, SYNC_SUCCESS
from ...shared.sync_operation_types import SYNC_CREATE

from ...models_access import ProductSyncAccess
from ...models_access import AmazonProductAccess
from ...models_access import OdooProductAccess

_logger = logging.getLogger(__name__)


class ProductCreationSuccess(object):
    def __init__(self, env):
        self._product_sync = ProductSyncAccess(env)
        self._amazon_product = AmazonProductAccess(env)
        self._odoo_product = OdooProductAccess(env)
        self._is_new_sync_added = False

    def _add_price_sync(self, record, completed):
        price = record[PRODUCT_PRICE_FIELD]
        self._product_sync.insert_price(completed, price)

    def _add_inventory_sync(self, record, completed):
        inventory = record[PRODUCT_AVAILABLE_QUANTITY_FIELD]
        self._product_sync.insert_inventory(completed, inventory)

    def _add_success_syncs(self, record, completed):
        self._add_price_sync(record, completed)
        self._add_inventory_sync(record, completed)
        self._product_sync.insert_image(completed)

    def _write_creation_success(self, completed):
        if self._odoo_product.is_sync_active(completed):
            record = self._odoo_product.browse(completed)
            self._add_success_syncs(record, completed)
            self._is_new_sync_added = True

    def _add_relation_sync(self, completed):
        # It is possible that a product template or variant
        # creation is failed and the relation
        # is not created for a product variant.
        # The automatic way to fix this is to create
        # relation syn for both template and variant creation sync
        if completed[MODEL_NAME_FIELD] == PRODUCT_PRODUCT_TABLE:
            template_head = {
                MODEL_NAME_FIELD: PRODUCT_TEMPLATE_TABLE,
                RECORD_ID_FIELD: completed[TEMPLATE_ID_FIELD],
            }
            if self._amazon_product.is_created(template_head):
                self._product_sync.insert_relation(completed)
            else:
                log_template = "Product template is not created for {}. " \
                               "Don't create relation sync."
                _logger.debug(log_template.format(
                    completed[RECORD_ID_FIELD]
                ))
        else:
            template_id = completed[RECORD_ID_FIELD]
            created_variants = self._amazon_product.get_variants(template_id)
            for variant in created_variants:
                self._product_sync.insert_relation(variant)

    def process(self, done_set):
        for done in done_set:
            # for warning and success, set success flag
            done_status = done[SYNC_STATUS_FIELD]
            is_success = (done_status == SYNC_SUCCESS or
                          done_status == SYNC_WARNING)
            is_sync_create = done[SYNC_TYPE_FIELD] == SYNC_CREATE
            if is_sync_create and is_success:
                log_template = "Post process creation success for " \
                               "product Model: {0}, Record Id: {1}."
                _logger.debug(log_template.format(
                    done[MODEL_NAME_FIELD], done[RECORD_ID_FIELD]))

                # make sure that the product is still there
                if self._odoo_product.is_existed(done):
                    # the order of the following calls matters because
                    # adding relation checks if a product is created or not
                    self._amazon_product.insert_completed(done)
                    self._write_creation_success(done)
                    self._add_relation_sync(done)
                else:
                    _logger.debug("Skip creation success for "
                                  "unlinked product.")
        return self._is_new_sync_added
