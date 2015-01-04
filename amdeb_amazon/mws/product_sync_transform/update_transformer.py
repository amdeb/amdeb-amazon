# -*- coding: utf-8 -*-

# import cPickle
import logging

from ...shared.model_names import (
    PRODUCT_NAME_FIELD,
)
from .base_transfomer import BaseTransformer

_logger = logging.getLogger(__name__)


class UpdateTransformer(BaseTransformer):
    """
    This class transform update values to update message fields
    """
    def _convert_update(self, sync_op):
        sync_value = super(UpdateTransformer, self)._convert_sync(sync_op)
        sync_value['Title'] = self._product[PRODUCT_NAME_FIELD]
        return sync_value
