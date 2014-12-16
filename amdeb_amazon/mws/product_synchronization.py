# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from ..shared.model_names import (
    IR_VALUES_TABLE,
    AMAZON_SETTINGS_TABLE,
)
from .connector import Boto
from .product_operation_transformer import ProductOperationTransformer
from .product_sync_new import ProductSyncNew
from .product_sync_pending import ProductSyncPending
from .product_sync_chore import do_daily_chore
from .product_sync_completed import ProductSyncCompleted


class ProductSynchronization(object):

    def __init__(self, env):
        self._env = env
        ir_values = env[IR_VALUES_TABLE]
        settings = ir_values.get_defaults_dict(AMAZON_SETTINGS_TABLE)
        self._mws = Boto(settings)

    def synchronize(self):
        """
        synchronize product operations to Amazon
        This is the entry to all product synchronization functions
        There are several steps:
        1. convert new product operations to sync operations
        2. execute sync operations and update end timestamp
        3. get sync results for pending sync operations and update
        end timestamp. This als process completed syncs
        4. process successful creation syncs

        Be aware that records may not exist when sync runs
        """
        _logger.debug("enter ProductSynchronization synchronize()")

        transformer = ProductOperationTransformer(self._env)
        transformer.transform()

        sync_new = ProductSyncNew(self._env, self._mws)
        sync_new.synchronize()

        sync_pending = ProductSyncPending(self._env, self._mws)
        sync_pending.synchronize()

        sync_completed = ProductSyncCompleted(self._env, self._mws)
        if sync_completed.synchronize():
            sync_new.synchronize()

        do_daily_chore(self._env)
