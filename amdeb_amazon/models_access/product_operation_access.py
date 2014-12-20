# -*- coding: utf-8 -*-

import logging
from ..shared.model_names import (
    PRODUCT_OPERATION_TABLE,
    AMAZON_SYNC_TIMESTAMP_FIELD,
)
from ..shared.utility import field_utcnow

_logger = logging.getLogger(__name__)


class ProductOperationAccess(object):
    """
    Get new product operations and set operation sync timestamp
    """
    def __init__(self, env):
        self._table = self.env[PRODUCT_OPERATION_TABLE]

    def get_new_operations(self):
        """
        Get the new operations ordered by descending id (creation time)
        A new operation doesn't have a sync timestamp
        """
        search_domain = [
            (AMAZON_SYNC_TIMESTAMP_FIELD, '=', False),
        ]
        operations = self._table.search(search_domain, order="id desc")

        _logger.debug("Found {0} new product operations. Ids: {1}.".format(
            len(operations), operations.ids
        ))
        return operations

    def set_sync_timestamp(self, operations):
        # set sync timestamp for each operation
        _logger.debug("set sync timestamp for all new product operations.")
        value = {AMAZON_SYNC_TIMESTAMP_FIELD: field_utcnow()}
        operations.write(value)
