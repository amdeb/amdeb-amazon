# -*- coding: utf-8 -*-

import logging

from ...models_access import (
    ProductSyncAccess,
    OdooProductAccess,
    AmazonProductAccess,
)
from ...model_names.product_template import PRODUCT_TEMPLATE_TABLE
from ...model_names.shared_names import (
    MODEL_NAME_FIELD, TEMPLATE_ID_FIELD, RECORD_ID_FIELD,
)
from ...model_names.product_sync import SYNC_CREATE

_logger = logging.getLogger(__name__)


class ProductCreateTransformer(object):
    """
    Transform create operation to a create sync.
    Ignore a create operation if it is from a partial variant
    """
    def __init__(self, env):
        self._product_sync = ProductSyncAccess(env)
        self._odoo_product = OdooProductAccess(env)
        self._amazon_product = AmazonProductAccess(env)

    def _insert_operation_sync(self, operation, product_sku):
        self._product_sync.insert_sync(operation, SYNC_CREATE)
        self._amazon_product.upsert_creation(operation, product_sku)

    def _insert_template_sync(self, operation, template_sku):
        template_head = {
            MODEL_NAME_FIELD: PRODUCT_TEMPLATE_TABLE,
            RECORD_ID_FIELD: operation[TEMPLATE_ID_FIELD],
            TEMPLATE_ID_FIELD: operation[TEMPLATE_ID_FIELD],
        }
        # we don't check whether the template is created in Amazon
        # or not. Usually all variants are created in a batch.
        is_inserted = self._product_sync.insert_sync_if_new(
            template_head, SYNC_CREATE)
        if is_inserted:
            _logger.debug("A template creation sync is inserted "
                          "for this non-partial variant.")
            self._amazon_product.upsert_creation(template_head, template_sku)

    def _add_variant_creation(self, operation, product):
        # need to check SKU for both variant and template
        product_sku = OdooProductAccess.get_sku(product)
        template_sku = OdooProductAccess.get_template_sku(product)

        if product_sku and template_sku:
            self._insert_operation_sync(operation, product_sku)
            self._insert_template_sync(operation, template_sku)
        else:
            _logger.debug("The product variant or its template "
                          "does not has a SKU, insert error sync.")
            self._product_sync.insert_sync(operation, SYNC_CREATE,
                                           error_flag=True)

    def _add_template_creation(self, operation, product):
        product_sku = OdooProductAccess.get_sku(product)
        if product_sku:
            self._insert_operation_sync(operation, product_sku)
        else:
            _logger.debug("The product template does not has a SKU, "
                          "insert error sync.")
            self._product_sync.insert_sync(operation, SYNC_CREATE,
                                           error_flag=True)

    def transform(self, operation):
        # Ignore partial variant creation because there is always a
        # template creation.
        # For non-partial variants, because its template maybe not create
        # or out-of-date, always add a template creation.
        # The correct approach to create variants is to create them
        # from a template in a single batch in Odoo

        # we check SKU here because Amazon product needs this field
        product = self._odoo_product.get_product(operation)
        is_variant = OdooProductAccess.is_product_variant(product)
        is_partial_variant = OdooProductAccess.is_partial_variant(product)
        is_mv_template = OdooProductAccess.is_multi_variant_template(product)
        if is_partial_variant or is_mv_template:
            _logger.debug("Skip partial variant or multi-variant template "
                          "creation operation.")
        elif is_variant:
            self._add_variant_creation(operation, product)
        else:
            self._add_template_creation(operation, product)
