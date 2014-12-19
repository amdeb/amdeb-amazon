# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from ..shared.model_names import (
    MODEL_NAME_FIELD,
    RECORD_ID_FIELD,

    PRODUCT_TEMPLATE_TABLE,
    PRODUCT_VARIANT_COUNT_FIELD,

    PRODUCT_PRODUCT_TABLE,
    TEMPLATE_ID_FIELD,
)

from .product_sync_access import ProductSyncAccess


class ProductCreateTransformer(object):
    def __init__(self, env):
        self._env = env
        self._product_sync = ProductSyncAccess(env)

    def _has_multi_variants(self, operation):
        result = False
        template = self._env[PRODUCT_TEMPLATE_TABLE]
        record = template.browse(operation[TEMPLATE_ID_FIELD])
        if record[PRODUCT_VARIANT_COUNT_FIELD] > 1:
            result = True
        return result

    def transform(self, operation):
        # ignore variant creation if it is the only variant
        model_name = operation[MODEL_NAME_FIELD]
        if model_name == PRODUCT_PRODUCT_TABLE:
            if not self._has_multi_variants(operation):
                log_template = "Skip single variant creation " \
                               "operation. Model: {0}, Record id: {1}"
                _logger.debug(log_template.format(
                    operation[MODEL_NAME_FIELD], operation[RECORD_ID_FIELD]
                ))
                return

        self._product_sync.insert_create(operation)
