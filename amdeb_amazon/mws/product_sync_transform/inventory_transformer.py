# -*- coding: utf-8 -*-

from ...model_names.product_product import PRODUCT_VIRTUAL_AVAILABLE_FIELD
from .base_transfomer import BaseTransformer
from ..amazon_names import AMAZON_QUANTITY_FIELD


class InventoryTransformer(BaseTransformer):

    def _convert_sync(self, sync_op):
        sync_value = super(InventoryTransformer, self)._convert_sync(sync_op)

        # The quantity must be an integer
        quantity = int(self._product[PRODUCT_VIRTUAL_AVAILABLE_FIELD])
        sync_value[AMAZON_QUANTITY_FIELD] = quantity
        return sync_value
