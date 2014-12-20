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
from .product_syncs import ProductCreationSuccess

_logger = logging.getLogger(__name__)


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
        """
        _logger.debug("Enter ProductSynchronization synchronize()")

        operation_access = ProductOperationAccess(self._env)
        new_operations = operation_access.get_new_operations()
        if new_operations:
            operation_access.set_sync_timestamp(new_operations)
            transformer = ProductOperationTransformer(self._env, new_operations)
            transformer.transform()

            sync_new = ProductSyncNew(self._env, self._mws)
            sync_new.synchronize()

        sync_pending = ProductSyncPending(self._env, self._mws)
        sync_pending.synchronize()

        sync_done = ProductSyncDone(self._env, self._mws)
        done_set = sync_done.synchronize()

        # create relation sync in a separate step because we need
        # to know the creation status of both the template and the variant
        if done_set:
            creation_success = ProductCreationSuccess(self._env)
            if creation_success.process(done_set):
                sync_new.synchronize()

        do_daily_chore(self._env)
