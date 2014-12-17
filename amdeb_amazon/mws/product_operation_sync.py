# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from ..shared.model_names import (
    PRODUCT_OPERATION_TABLE,
    AMAZON_SYNC_TIMESTAMP_FIELD,
)

from ..shared.utility import field_utcnow


class ProductOperationSync(object):
    """
    Get new product operations and set operation sync timestamp
    """
    def __init__(self, env):
        self._env = env

    def get_new_operations(self):
        """
        Get the new operations ordered by descending id (creation time)
        A new operation doesn't have a sync timestamp
        """
        operation_table = self._env[PRODUCT_OPERATION_TABLE]
        search_domain = [
            (AMAZON_SYNC_TIMESTAMP_FIELD, '=', False),
        ]
        new_operations = operation_table.search(
            search_domain,
            order="id desc")

        _logger.debug("Found {0} new product operations. Ids: {1}.".format(
            len(new_operations), new_operations.ids
        ))
        return new_operations

    def set_operation_sync_timestamp(self, operations):
        # set sync timestamp for each operation
        _logger.debug("set sync timestamp for all new product operations.")
        for operation in operations:
            operation[AMAZON_SYNC_TIMESTAMP_FIELD] = field_utcnow()
