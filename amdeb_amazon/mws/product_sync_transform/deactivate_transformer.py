# -*- coding: utf-8 -*-

from .base_transfomer import BaseTransformer
from ..amazon_names import AMAZON_QUANTITY_FIELD


class DeactivateTransformer(BaseTransformer):

    def _convert_sync(self, sync_op):
        sync_value = super(DeactivateTransformer, self)._convert_sync(sync_op)
        sync_value[AMAZON_QUANTITY_FIELD] = 0
        return sync_value
