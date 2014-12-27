# -*- coding: utf-8 -*-

import logging

from ...models_access import OdooProductAccess
from ...shared.model_names import (
    PRODUCT_DEFAULT_CODE_FIELD, PRODUCT_VIRTUAL_AVAILABLE_FIELD,
)

_logger = logging.getLogger(__name__)


class InventoryTransformer(object):
    """
    This class transform list price to Amazon sync message
    May support sales price in the future
    """
    def __init__(self, env):
        self._odoo_product = OdooProductAccess(env)

    def _convert_sync(self, sync_inventory):
        sync_value = {'ID': sync_inventory.id}
        product = self._odoo_product.browse(sync_inventory)
        sync_value['SKU'] = product[PRODUCT_DEFAULT_CODE_FIELD]

        # The quantity must be an integer
        sync_value['quantity'] = int(product[PRODUCT_VIRTUAL_AVAILABLE_FIELD])
        return sync_value

    def transform(self, sync_inventories):
        sync_values = []
        for sync_inventory in sync_inventories:
            sync_value = self._convert_sync(sync_inventory)
            if sync_value:
                sync_values.append(sync_value)
        return sync_values
