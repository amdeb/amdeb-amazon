# -*- coding: utf-8 -*-

from ..shared.model_names import (
    PRODUCT_TEMPLATE,
    PRODUCT_PRODUCT,
    PRODUCT_OPERATION_TABLE,
    AMAZON_SYNC_TIMESTAMP_FIELD,
    AMAZON_PRODUCT_SYNC_TABLE,
    # SYNC_CREATE,
    # SYNC_UPDATE,
    # SYNC_DELETE,
    # SYNC_PRICE,
    # SYNC_INVENTORY,
    # SYNC_IMAGE,
    # SYNC_DEACTIVATE,
)
from ..shared.utility import field_utcnow


class ProductOperationTransformer(object):
    """ Transform product operations into sync operations


    """
    def __init__(self, env):
        self.env = env
        self.product_template = self.env[PRODUCT_TEMPLATE]
        self.product_product = self.env[PRODUCT_PRODUCT]
        self.product_operation = self.env[PRODUCT_OPERATION_TABLE]
        self.amazon_sync = self.env[AMAZON_PRODUCT_SYNC_TABLE]

    def _get_operations(self):
        search_domain = [
            (AMAZON_SYNC_TIMESTAMP_FIELD, '=', False),
        ]
        operations = self.product_operation.search(search_domain)

        # set sync timestamp for each operation
        for operation in operations:
            operation[AMAZON_SYNC_TIMESTAMP_FIELD] = field_utcnow()
        return operations

    def transform(self):
        self._get_operations()
