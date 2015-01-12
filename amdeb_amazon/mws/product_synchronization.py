# -*- coding: utf-8 -*-

import logging

from ..shared.model_names import (
    IR_VALUES_TABLE, AMAZON_SETTINGS_TABLE,
)
from .connector import Boto
from ..models_access import ProductOperationAccess
from .product_operation_transform import ProductOperationTransformer
from .product_syncs import ProductSyncNew
from .product_syncs import ProductSyncPending
from .product_syncs import do_daily_chore
from .product_syncs import ProductSyncDone

_logger = logging.getLogger(__name__)


class ProductSynchronization(object):

    def __init__(self, env):
        self._env = env
        ir_values = env[IR_VALUES_TABLE]
        settings = ir_values.get_defaults_dict(AMAZON_SETTINGS_TABLE)
        self._mws = Boto(settings)

    def synchronize(self):
        """
        We need a good strategy to deal with request exception.
        1. Make all request idempotent by using the latest data in request
        2. When there is an exception, save current results and stop

        synchronize product operations to Amazon
        This is the entry to all product synchronization functions.
        We process old business first. There are several steps:
        1. do daily chore on sync table
        2. get sync results for pending sync operations
        3. process completed syncs
        4. get new operations and set sync timestamp
        5. convert new product operations to sync operations
        6. execute sync operations and save submission timestamp

        All calls report exception inside their methods because
        they should run independently.
        """
        _logger.debug("Enter ProductSynchronization synchronize()")

        do_daily_chore(self._env)

        sync_pending = ProductSyncPending(self._env, self._mws)
        sync_pending.synchronize()

        sync_done = ProductSyncDone(self._env, self._mws)
        sync_done.synchronize()

        operation_access = ProductOperationAccess(self._env)
        new_operations = operation_access.search_new_operations()
        if new_operations:
            operation_access.set_sync_timestamp(new_operations)

            transformer = ProductOperationTransformer(
                self._env, new_operations)
            transformer.transform()

        sync_new = ProductSyncNew(self._env, self._mws)
        sync_new.synchronize()
