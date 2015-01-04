# -*- coding: utf-8 -*-

import logging

from ...models_access import OdooProductAccess, ProductSyncAccess
from ...shared.model_names import PRODUCT_DEFAULT_CODE_FIELD

_logger = logging.getLogger(__name__)


class BaseTransformer(object):
    """
    This is the base transform
    """
    def __init__(self, env):
        self._odoo_product = OdooProductAccess(env)
        self._product_sync = ProductSyncAccess(env)
        self._product = None

    def _convert_sync(self, sync_op):
        sync_value = {'ID': sync_op.id}
        self._product = self._odoo_product.browse(sync_op)
        sku = self._product[PRODUCT_DEFAULT_CODE_FIELD]
        if sku:
            sku = sku.strip()
        if sku:
            sync_value['SKU'] = sku
        else:
            raise ValueError("Invalid SKU value in Sync transformation")
        return sync_value

    def transform(self, sync_ops):
        sync_values = []
        valid_ops = []
        for sync_op in sync_ops:
            try:
                sync_value = self._convert_sync(sync_op)
                sync_values.append(sync_value)
                valid_ops.append(sync_op)
            except Exception as ex:
                log_template = "Sync transform error {0} for sync id {1}."
                _logger.debug(log_template.format(sync_op.id, ex.message))
                self._product_sync.update_sync_new_exception(ex, sync_op)

        return sync_values
