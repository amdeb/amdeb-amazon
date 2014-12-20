# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from ...shared.model_names import (
    MODEL_NAME_FIELD,
    RECORD_ID_FIELD,

    PRODUCT_PRODUCT_TABLE,
    TEMPLATE_ID_FIELD,
)

from ...models_access import ProductSyncAccess
from ...models_access import OdooProductAccess


class ProductCreateTransformer(object):
    def __init__(self, env):
        self._env = env
        self._product_sync = ProductSyncAccess(env)
        self._odoo_product = OdooProductAccess(env)

    def transform(self, operation):
        # ignore variant creation if it is the only variant
        single_variant = False
        model_name = operation[MODEL_NAME_FIELD]
        if model_name == PRODUCT_PRODUCT_TABLE:
            template_id = operation[TEMPLATE_ID_FIELD]
            if not self._odoo_product.has_multi_variants(template_id):
                single_variant = True

        if single_variant:
            log_template = "Skip single variant creation " \
                           "operation. Model: {0}, Record id: {1}"
            _logger.debug(log_template.format(
                operation[MODEL_NAME_FIELD], operation[RECORD_ID_FIELD]
            ))
        else:
            self._product_sync.insert_create(operation)
