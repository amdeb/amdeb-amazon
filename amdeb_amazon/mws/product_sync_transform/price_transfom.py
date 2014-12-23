# -*- coding: utf-8 -*-
import datetime
import logging

from ...models_access import OdooProductAccess
from ...shared.model_names import (
    PRODUCT_DEFAULT_CODE_FIELD, PRODUCT_PRICE_FIELD,
    PRODUCT_LIST_PRICE_FIELD,
)
from ...shared.utility import MWS_DATETIME_FORMAT

_SALE_END_DAYS = 1000

_logger = logging.getLogger(__name__)


class PriceTransformer(object):
    """
    This class transform list price and sales price to Amazon sync message
    """
    def __init__(self, env):
        self._odoo_product = OdooProductAccess(env)

    def _convert_sync(self, sync_price):
        sync_value = {'ID': sync_price.id}
        product = self._odoo_product.browse(sync_price)
        sync_value['SKU'] = product[PRODUCT_DEFAULT_CODE_FIELD]

        sync_value['StandardPrice'] = product[PRODUCT_LIST_PRICE_FIELD]

        sale_price = product[PRODUCT_PRICE_FIELD]
        sync_value['SalePrice'] = sale_price

        # we don't know if there is a sale price in Amazon,
        # thus enable or disable it here
        start_date = datetime.datetime.utcnow()
        start_date_str = start_date.strftime(MWS_DATETIME_FORMAT)
        sync_value['StartDate'] = start_date_str
        if sync_value['StandardPrice'] == sale_price:
            # set to current time to disable it
            sync_value['EndDate'] = start_date_str
        else:
            end_date = start_date + datetime.timedelta(days=_SALE_END_DAYS)
            sync_value['EndDate'] = end_date.strftime(MWS_DATETIME_FORMAT)
        return sync_value

    def transform(self, sync_prices):
        sync_values = []
        for sync_price in sync_prices:
            sync_value = self._convert_sync(sync_price)
            if sync_value:
                sync_values.append(sync_value)
        return sync_values
