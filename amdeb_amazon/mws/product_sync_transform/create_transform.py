# -*- coding: utf-8 -*-

import logging

from ...shared.model_names import (
    PRODUCT_NAME_FIELD,
)
from .base_transfomer import BaseTransformer

_logger = logging.getLogger(__name__)


class CreateTransformer(BaseTransformer):
    def _convert_create(self, sync_op):
        sync_value = super(CreateTransformer, self)._convert_sync(sync_op)

        sync_value['Title'] = self._product[PRODUCT_NAME_FIELD]
        return sync_value
