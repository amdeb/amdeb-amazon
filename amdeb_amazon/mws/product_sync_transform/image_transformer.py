# -*- coding: utf-8 -*-

import logging

from ...models_access import OdooProductAccess
from ...shared.model_names import (
    PRODUCT_DEFAULT_CODE_FIELD,
)

_logger = logging.getLogger(__name__)


class ImageTransformer(object):
    """
    This class transform list price to Amazon sync message
    May support sales price in the future
    """
    def __init__(self, env):
        self._odoo_product = OdooProductAccess(env)

    def _convert_sync(self, sync_price):
        sync_value = {'ID': sync_price.id}
        product = self._odoo_product.browse(sync_price)
        sync_value['SKU'] = product[PRODUCT_DEFAULT_CODE_FIELD]
        return sync_value

    def transform(self, sync_prices):
        sync_values = []
        for sync_price in sync_prices:
            sync_value = self._convert_sync(sync_price)
            if sync_value:
                sync_values.append(sync_value)
        return sync_values
