# -*- coding: utf-8 -*-

import logging
from ...models_access import ProductSyncAccess
from ...models_access import OdooProductAccess
from ...shared.model_names import (
    MODEL_NAME_FIELD,
    PRODUCT_TEMPLATE_TABLE, TEMPLATE_ID_FIELD,
    RECORD_ID_FIELD,
)


_logger = logging.getLogger(__name__)


class ProductCreateTransformer(object):
    """
    Transform create operation to a create sync.
    Ignore a create operation if it is from a partial variant
    """
    def __init__(self, env):
        self._product_sync = ProductSyncAccess(env)
        self._odoo_product = OdooProductAccess(env)

    def transform(self, operation):
        # Ignore variant creation if it is the only variant
        # because a user usually deletes template, not the partial variant.
        # For non-partial variant, insert the create sync for its template
        # Thus we need to check existence of multi-variant template create
        if OdooProductAccess.is_product_variant(operation):
            if self._odoo_product.is_partial_variant(operation):
                _logger.debug("Skip partial variant creation operation.")
            else:
                self._product_sync.insert_create(operation)
                template_head = {
                    MODEL_NAME_FIELD: PRODUCT_TEMPLATE_TABLE,
                    RECORD_ID_FIELD: operation[TEMPLATE_ID_FIELD],
                    TEMPLATE_ID_FIELD: operation[TEMPLATE_ID_FIELD],
                }
                # we don't check whether the template is created in Amazon
                # or not. Usually all variants are created in a batch.
                self._product_sync.insert_create_if_new(template_head)
        else:
            template = self._odoo_product.browse(operation)
            if self._odoo_product.has_multi_variants(template):
                # template create sync is inserted by one of its variants
                log_template = "Skip creation operation for template {} " \
                               "that has multi-variants."
                _logger.debug(log_template.format(operation))
            else:
                self._product_sync.insert_create(operation)
