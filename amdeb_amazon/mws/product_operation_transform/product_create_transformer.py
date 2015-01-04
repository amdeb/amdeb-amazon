# -*- coding: utf-8 -*-

import logging

from ...models_access import ProductSyncAccess
from ...models_access import OdooProductAccess

_logger = logging.getLogger(__name__)


class ProductCreateTransformer(object):
    """
    Transform create operation to a create sync.
    Ignore a create operation if it is from a partial variant
    """
    def __init__(self, env):
        self._product_sync = ProductSyncAccess(env)
        self._odoo_product = OdooProductAccess(env)

    def transform(self, operation):
        # ignore variant creation if it is the only variant
        # thus the amazon product is_created is False for partial variant
        if self._odoo_product.is_partial_variant(operation):
            _logger.debug("Skip partial variant creation operation.")
        else:
            self._product_sync.insert_create(operation)
