# -*- coding: utf-8 -*-

import logging

from ...models_access import OdooProductAccess
from ...shared.model_names import (
    PRODUCT_DEFAULT_CODE_FIELD,
    PRODUCT_NAME_FIELD,
)

_logger = logging.getLogger(__name__)


class CreateTransformer(object):
    """
    This class transform update values to update message fields
    """
    def __init__(self, env):
        self._odoo_product = OdooProductAccess(env)

    def _convert_create(self, sync_create):
        sync_value = {}

        sync_value['ID'] = sync_create.id
        # SKU can not be changed after creation
        product = self._odoo_product.browse(sync_create)
        sync_value['SKU'] = product[PRODUCT_DEFAULT_CODE_FIELD]
        sync_value['Title'] = product[PRODUCT_NAME_FIELD]

        return sync_value

    def transform(self, sync_creates):
        sync_values = []
        for sync_create in sync_creates:
            sync_value = self._convert_create(sync_create)
            if sync_value:
                sync_values.append(sync_value)
        return sync_values
