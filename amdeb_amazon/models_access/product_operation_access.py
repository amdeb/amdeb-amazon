# -*- coding: utf-8 -*-

import logging
from ..shared.model_names import (
    PRODUCT_OPERATION_TABLE,
    AMAZON_SYNC_TIMESTAMP_FIELD,
)
from ..shared.utility import field_utcnow
from .sync_head_access import SyncHeadAccess

_logger = logging.getLogger(__name__)


class ProductOperationAccess(SyncHeadAccess):
    """
    Get new product operations and set operation sync timestamp
    """
    def __init__(self, env):
        self._table = env[PRODUCT_OPERATION_TABLE]

    def get_new_operations(self):
        """
        Get the new operations ordered by descending id (creation time)
        A new operation doesn't have a sync timestamp
        """
        search_domain = [
            (AMAZON_SYNC_TIMESTAMP_FIELD, '=', False),
        ]
        operations = self._table.search(search_domain, order="id desc")

        log_template = "Found {0} new product operations. Ids: {1}."
        _logger.debug(log_template.format(len(operations), operations.ids))
        return operations

    @staticmethod
    def set_sync_timestamp(operations):
        # set sync timestamp for each operation
        _logger.debug("set sync timestamp for all new product operations.")
        value = {AMAZON_SYNC_TIMESTAMP_FIELD: field_utcnow()}
        operations.write(value)
