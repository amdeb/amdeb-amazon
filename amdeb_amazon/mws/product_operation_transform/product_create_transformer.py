# -*- coding: utf-8 -*-

import logging
from ...models_access import ProductSyncAccess
from ...models_access import OdooProductAccess
from ...models_access import AmazonProductAccess
from ...shared.model_names import (
    PRODUCT_TEMPLATE_TABLE,
)
from ...shared.model_names.shared_names import (
    MODEL_NAME_FIELD, TEMPLATE_ID_FIELD, RECORD_ID_FIELD,
)
from ...shared.sync_operation_types import SYNC_CREATE

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

    def transform(self, operation):
        # Ignore partial variant creation because there is always a
        # template creation.
        # For non-partial variants, because its template maybe not create
        # or out-of-date, always add a template creation.
        # The correct approach to create variants is to create them
        # from a template in a single batch in Odoo

        # because we always insert a create for template, we can
        # skip update syncs in the same sync batch.
        product = self._odoo_product.get_product(operation)
        if OdooProductAccess.is_product_variant(product):
            if OdooProductAccess.is_partial_variant(product):
                _logger.debug("Skip partial variant creation operation.")
            else:
                self._product_sync.insert_sync(operation, SYNC_CREATE)
                self._amazon_product.upsert_creation(operation)
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
                    self._amazon_product.upsert_creation(template_head)
        else:
            if OdooProductAccess.is_multi_variant_template(product):
                # template create sync is inserted by one of its variants
                _logger.debug("Skip creation operation for multi-variant "
                              "template that is created with its variants.")
            else:
                self._product_sync.insert_sync(operation, SYNC_CREATE)
                self._amazon_product.upsert_creation(operation)
