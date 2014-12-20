# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from ...shared.model_names import (
    PRODUCT_PRODUCT_TABLE, MODEL_NAME_FIELD, RECORD_ID_FIELD,
)

from ...models_access import ProductSyncAccess
from ...models_access import OdooProductAccess


class ProductCreateTransformer(object):
    def __init__(self, env):
        self._product_sync = ProductSyncAccess(env)
        self._odoo_product = OdooProductAccess(env)

    def transform(self, operation):
        # ignore variant creation if it is the only variant
        partial_variant = False
        model_name = operation[MODEL_NAME_FIELD]
        record_id = operation[RECORD_ID_FIELD]
        log_template = "Transform create operation for " \
                       "Model: {0}, Record id: {1}."
        _logger.debug(log_template.format(
            model_name, record_id))

        if model_name == PRODUCT_PRODUCT_TABLE:
            if self._odoo_product.is_partial_variant(record_id):
                partial_variant = True

        if partial_variant:
            _logger.debug("Skip single variant creation operation.")
        else:
            self._product_sync.insert_create(operation)
