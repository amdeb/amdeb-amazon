# -*- coding: utf-8 -*-

import cPickle
import logging
_logger = logging.getLogger(__name__)

from ...shared.model_names import (
    PRODUCT_DEFAULT_CODE_FIELD, SYNC_DATA_FIELD,
)
from ...models_access import OdooProductAccess


class UpdateTransformer(object):
    """
    This class transform update values to update message fields
    """
    def __init__(self, env):
        self._odoo_product = OdooProductAccess(env)

    def _get_sku(self, sync_update, sync_data):
        sku = sync_data[PRODUCT_DEFAULT_CODE_FIELD]
        if not sku:
            sku = self._odoo_product.get_sku(sync_update)
        return sku

    def _convert_update(self, sync_update):
        sync_value = {}
        sync_data = cPickle.loads(sync_update[SYNC_DATA_FIELD])

        sync_value['ID'] = sync_update.id
        sync_value['SKU'] = self._get_sku(sync_update, sync_data)

        sync_value['Title'] = sync_data['name']

        return sync_value

    def transform(self, sync_updates):
        sync_values = []
        for sync_update in sync_updates:
            sync_value = self._convert_update(sync_update)
            if sync_value:
                sync_values.append(sync_value)
        return sync_values
