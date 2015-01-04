# -*- coding: utf-8 -*-

from .base_transfomer import BaseTransformer
from ...shared.model_names import PRODUCT_VIRTUAL_AVAILABLE_FIELD


class InventoryTransformer(BaseTransformer):

    def _convert_sync(self, sync_op):
        sync_value = super(InventoryTransformer, self)._convert_sync(sync_op)

        # The quantity must be an integer
        quantity = int(self._product[PRODUCT_VIRTUAL_AVAILABLE_FIELD])
        sync_value['quantity'] = quantity
        return sync_value
