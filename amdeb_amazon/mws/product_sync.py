# -*- coding: utf-8 -*-

# this class is the entry to all product synchronization functions
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)

from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

from .connector import Boto
from .product_operation_transformer import ProductOperationTransformer
from .product_sync_new import ProductSyncNew
from .product_sync_pending import ProductSyncPending
from ..shared.model_names import (
    AMAZON_PRODUCT_SYNC_TABLE,
    SYNC_CREATION_TIMESTAMP_FIELD,
    SYNC_STATUS_FIELD,
    SYNC_CHECK_STATUS_COUNT_FILED,
    AMAZON_MESSAGE_CODE_FIELD,
    AMAZON_RESULT_DESCRIPTION_FIELD
)
from ..shared.sync_status import (
    SYNC_PENDING,
    SYNC_ERROR,
)

_UNLINK_DAYS = 100
_ARCHIVE_MAGIC_NUMBER = 10
_ARCHIVE_CODE = "Timeout"
_ARCHIVE_MESSAGE = "Pending more than {0} days and checked {0} times".format(
    _ARCHIVE_MAGIC_NUMBER
)


class ProductSynchronization(object):
    _last_housekeeping_date = None

    def __init__(self, env):
        self._env = env
        self._mws = Boto(env)
        self._amazon_sync = self._env[AMAZON_PRODUCT_SYNC_TABLE]

    def _cleanup(self):
        _logger.debug("running product synchronization cleanup")
        now = datetime.utcnow()
        unlink_date = now - timedelta(days=_UNLINK_DAYS)
        unlink_date_str = unlink_date.strftime(DATETIME_FORMAT)
        unlink_records = self._amazon_sync.search([
            (SYNC_CREATION_TIMESTAMP_FIELD, '<', unlink_date_str)
        ])
        unlink_records.unlink()

    def _archive_old(self):
        _logger.debug("running product synchronization archive old")
        now = datetime.utcnow()
        archive_date = now - timedelta(days=_ARCHIVE_MAGIC_NUMBER)
        archive_date_str = archive_date.strftime(DATETIME_FORMAT)
        archive_records = self._amazon_sync.search([
            (SYNC_CREATION_TIMESTAMP_FIELD, '<', archive_date_str),
            (SYNC_STATUS_FIELD, '=', SYNC_PENDING),
            (SYNC_CHECK_STATUS_COUNT_FILED, '>=', _ARCHIVE_MAGIC_NUMBER)
        ])
        archive_status = {
            SYNC_STATUS_FIELD: SYNC_ERROR,
            AMAZON_MESSAGE_CODE_FIELD: _ARCHIVE_CODE,
            AMAZON_RESULT_DESCRIPTION_FIELD: _ARCHIVE_MESSAGE
        }
        archive_records.write(archive_status)

    def _daily_housekeeping(self):
        run = False
        current_day = datetime.date.today()
        if ProductSynchronization._last_housekeeping_date:
            diff = current_day - ProductSynchronization._last_housekeeping_date
            if diff.days > 0:
                run = True
        else:
            run = True

        if run:
            ProductSynchronization._last_housekeeping_date = current_day
            self._cleanup()
            self._archive_old()

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
        _logger.debug("running product synchronize()")

        transformer = ProductOperationTransformer(self._env)
        transformer.transform()

        sync_new = ProductSyncNew(self._env, self._mws)
        sync_new.synchronize()

        sync_pending = ProductSyncPending(self._env, self._mws)
        sync_pending.synchronize()

        self._daily_housekeeping()
