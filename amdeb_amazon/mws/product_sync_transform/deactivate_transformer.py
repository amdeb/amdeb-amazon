# -*- coding: utf-8 -*-

from .base_transfomer import BaseTransformer


class DeactivateTransformer(BaseTransformer):

    def _convert_sync(self, sync_op):
        sync_value = super(DeactivateTransformer, self)._convert_sync(sync_op)
        sync_value['quantity'] = 0
        return sync_value
