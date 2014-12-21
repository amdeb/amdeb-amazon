# -*- coding: utf-8 -*-

import logging

from ...shared.model_names import (
    PRODUCT_PRODUCT_TABLE, MODEL_NAME_FIELD,
)
from ...models_access import ProductSyncAccess
from ...models_access import OdooProductAccess

_logger = logging.getLogger(__name__)


class ProductCreateTransformer(object):
    """
    Transform create operation to a create sync.
    Ignore a create operation if it is from a partial variant
    """
    def __init__(self, env):
        self._product_sync = ProductSyncAccess(env)
        self._odoo_product = OdooProductAccess(env)

    def _is_partial_variant(self, operation):
        partial_variant = False
        if operation[MODEL_NAME_FIELD] == PRODUCT_PRODUCT_TABLE:
            if self._odoo_product.is_partial_variant(operation):
                partial_variant = True

        return partial_variant

    def transform(self, operation):
        # ignore variant creation if it is the only variant
        # thus the amazon product is_created is False for partial variant
        if self._is_partial_variant(operation):
            _logger.debug("Skip single variant creation operation.")
        else:
            self._product_sync.insert_create(operation)
