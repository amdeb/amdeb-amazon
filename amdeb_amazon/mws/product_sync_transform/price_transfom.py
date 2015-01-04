# -*- coding: utf-8 -*-

import logging

from ...shared.model_names import PRODUCT_LST_PRICE_FIELD
from .base_transfomer import BaseTransformer

_logger = logging.getLogger(__name__)


class PriceTransformer(BaseTransformer):
    """
    This class transform list price to Amazon sync message
    May support sales price in the future
    """

    def _convert_sync(self, sync_op):
        sync_value = super(PriceTransformer, self)._convert_sync(sync_op)
        # The 'lst_price' has the extra price for variant
        standard_price = self._product[PRODUCT_LST_PRICE_FIELD]
        if standard_price >= 0.01:
            sync_value['StandardPrice'] = self._product[
                PRODUCT_LST_PRICE_FIELD]
        else:
            message = "Invalid price {} in Sync transformation".format(
                standard_price)
            raise ValueError(message)
        return sync_value
