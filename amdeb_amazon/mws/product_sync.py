# -*- coding: utf-8 -*-

# this class is the entry to all product synchronization functions

from ..shared.model_names import (
    PRODUCT_OPERATION_TABLE,
    PRODUCT_TEMPLATE,
    PRODUCT_PRODUCT,
)

from .product_operation_transformer import ProductOperationTransformer
from .product_sync_new import ProductSyncNew


class ProductSynchronization(object):
    def __init__(self, env):
        self.env = env
        self.product_operations = self.env[PRODUCT_OPERATION_TABLE]
        self.product_template = self.env[PRODUCT_TEMPLATE]
        self.product_product = self.env[PRODUCT_PRODUCT]

    def synchronize(self):
        ''' synchronize product operations to Amazon
        There are several steps:
        1. convert new product operations to sync operations
        2. execute sync operations and update end timestamp
        3. get sync results for pending sync operations and update
        end timestamp
        4. create and execute new price, image and inventory sync
        operations for successful create sync operation
        '''
        transformer = ProductOperationTransformer(self.env)
        transformer.transform()

        sync_new = ProductSyncNew(self.env)
        sync_new.synchronize()

        # mws = self._get_mws()
        # self._sync_product(mws, operations)
