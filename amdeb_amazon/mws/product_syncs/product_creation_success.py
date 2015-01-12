# -*- coding: utf-8 -*-

import logging

from ...shared.model_names import (
    PRODUCT_TEMPLATE_TABLE,
    MODEL_NAME_FIELD, RECORD_ID_FIELD,
    SYNC_STATUS_FIELD, TEMPLATE_ID_FIELD,
)
from ...shared.sync_status import SYNC_STATUS_WARNING, SYNC_STATUS_SUCCESS
from ...shared.sync_operation_types import (
    SYNC_RELATION, SYNC_PRICE,
    SYNC_IMAGE, SYNC_INVENTORY,
)
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

    def _add_success_syncs(self, completed):
        product = self._odoo_product.get_product(completed)
        sync_active = OdooProductAccess.is_sync_active_product(product)
        is_partial_variant = OdooProductAccess.is_partial_variant(product)
        multi_template = OdooProductAccess.is_multi_variant_template(product)
        if sync_active and not is_partial_variant and not multi_template:
            self._product_sync.insert_sync(completed, SYNC_PRICE)
            self._product_sync.insert_sync(completed, SYNC_INVENTORY)
            self._product_sync.insert_sync(completed, SYNC_IMAGE)
            self._is_new_sync_added = True

    def _add_relation_sync(self, completed):
        # It is possible that a product template or variant
        # creation is failed and the relation
        # is not created for a product variant.
        # The automatic way to fix this is to create
        # relation syn for both template and variant creation sync
        # we only add a sync for the template with at least one variant
        # created successfully in Amazon
        if ProductSyncAccess.is_product_variant(completed):
            template_head = {
                MODEL_NAME_FIELD: PRODUCT_TEMPLATE_TABLE,
                RECORD_ID_FIELD: completed[TEMPLATE_ID_FIELD],
                TEMPLATE_ID_FIELD: completed[TEMPLATE_ID_FIELD]
            }
            if self._amazon_product.is_created_by_head(template_head):
                self._product_sync.insert_sync_if_new(
                    completed, SYNC_RELATION)
                self._is_new_sync_added = True
            else:
                log_template = "Product template is not created for a " \
                               "variant {}. Don't create relation sync."
                _logger.debug(log_template.format(
                    completed[RECORD_ID_FIELD]
                ))
        else:
            template_id = completed[RECORD_ID_FIELD]
            created_variants = self._amazon_product.get_variants(template_id)
            if created_variants:
                self._product_sync.insert_sync_if_new(
                    completed, SYNC_RELATION)
                self._is_new_sync_added = True

    def process(self, done_sync):
        if not self._odoo_product.get_existed_product(done_sync):
            _logger.debug("Skip creation success for unlinked product.")

        done_status = done_sync[SYNC_STATUS_FIELD]
        log_template = "Post creation process for product Model: {0}, " \
                       "Record Id: {1}, sync status: {2}."
        _logger.debug(log_template.format(
            done_sync[MODEL_NAME_FIELD],
            done_sync[RECORD_ID_FIELD], done_status))
        # for warning and success, set success flag
        is_success = (done_status == SYNC_STATUS_SUCCESS or
                      done_status == SYNC_STATUS_WARNING)
        if is_success:
            # the order of the following calls matters because
            # adding relation checks if a product is created or not
            self._amazon_product.update_created(done_sync)

            # old syncs first
            self._product_sync.update_waiting_to_new(done_sync)
            self._add_success_syncs(done_sync)
            self._add_relation_sync(done_sync)
        else:
            self._amazon_product.update_error(done_sync)
