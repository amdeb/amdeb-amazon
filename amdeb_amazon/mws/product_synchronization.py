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
        2. When there is an exception, save current results, report and
        swallow the exception.

        synchronize product operations to Amazon
        This is the entry to all product synchronization functions.
        We process old business first. There are several steps:
        1. do daily chore on sync table
        2. get sync status for pending sync operations
        3. process completed syncs
        4. get new product operations and set sync timestamp
        5. convert new product operations to sync operations
        6. send syncs to Amazon

        All stages swallows exception because each stage retrieves
        data from database
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
