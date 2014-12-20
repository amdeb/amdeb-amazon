# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from ...shared.model_names import (
    PRODUCT_PRODUCT_TABLE, MODEL_NAME_FIELD, RECORD_ID_FIELD,
)

from ...models_access import ProductSyncAccess
from ...models_access import OdooProductAccess


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
            record_id = operation[RECORD_ID_FIELD]
            if self._odoo_product.is_partial_variant(record_id):
                partial_variant = True

        return partial_variant

    def transform(self, operation):
        log_template = "Transform create operation for " \
                       "Model: {0}, Record id: {1}."
        _logger.debug(log_template.format(
            operation[MODEL_NAME_FIELD], operation[RECORD_ID_FIELD]))

        # ignore variant creation if it is the only variant
        if self._is_partial_variant(operation):
            _logger.debug("Skip single variant creation operation.")
        else:
            self._product_sync.insert_create(operation)
