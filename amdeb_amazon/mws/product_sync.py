# -*- coding: utf-8 -*-

# this class is the entry to all product synchronization functions

from .connector import Boto

from .product_operation_transformer import ProductOperationTransformer
from .product_sync_new import ProductSyncNew
from .product_sync_pending import ProductSyncPending

class ProductSynchronization(object):
    def __init__(self, env):
        self._env = env
        self._mws = Boto(env)

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
        transformer = ProductOperationTransformer(self._env)
        transformer.transform()

        sync_new = ProductSyncNew(self._env, self._mws)
        sync_new.synchronize()

        sync_pending = ProductSyncPending(self._env, self._mws)
        sync_pending.synchronize()
