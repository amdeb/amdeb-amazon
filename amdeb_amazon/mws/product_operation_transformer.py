# -*- coding: utf-8 -*-

import cPickle
import logging

_logger = logging.getLogger(__name__)

from ..shared.model_names import (
    PRODUCT_TEMPLATE,
    PRODUCT_PRODUCT,
    PRODUCT_OPERATION_TABLE,
    AMAZON_SYNC_TIMESTAMP_FIELD,
    AMAZON_PRODUCT_SYNC_TABLE,
    # SYNC_CREATE,
    # SYNC_UPDATE,
    # SYNC_DELETE,
    # SYNC_PRICE,
    # SYNC_INVENTORY,
    # SYNC_IMAGE,
    # SYNC_DEACTIVATE,
)
from ..shared.utility import field_utcnow
from ..shared.operations_types import (
    CREATE_RECORD,
    WRITE_RECORD,
    UNLINK_RECORD,
)


class ProductOperationTransformer(object):
    """ Transform product operations into sync operations

    1. get new operations sorted by id
    2. set operation sync timestamps
    3. merge operations
    4. transform product operation into sync operations
    """

    def __init__(self, env):
        self.env = env
        self.product_template = self.env[PRODUCT_TEMPLATE]
        self.product_product = self.env[PRODUCT_PRODUCT]
        self.product_operation = self.env[PRODUCT_OPERATION_TABLE]
        self.amazon_sync = self.env[AMAZON_PRODUCT_SYNC_TABLE]
        self.processed = set()

    def _get_operations(self):
        search_domain = [
            (AMAZON_SYNC_TIMESTAMP_FIELD, '=', False),
        ]
        self.operations = self.product_operation.search(
            search_domain,
            order="id desc")

        # set sync timestamp for each operation
        for operation in self.operations:
            operation[AMAZON_SYNC_TIMESTAMP_FIELD] = field_utcnow()

    def _add_unlink_sync(self, operation):
        pass

    def _transform_unlink(self, operation):
        self._add_unlink_sync(operation)

        # assume that MWS has cascade delete -- TBD
        # remove all variant operations if this is a template unlink
        if operation.model_name == PRODUCT_TEMPLATE:
            ignored = [
                (variant.model_name, variant.record_id) for
                variant in self.operations if
                variant.model_name == PRODUCT_PRODUCT and
                variant.template_id == operation.record_id
            ]
            self.processed.update(ignored)

    def _add_create_sync(self, operation):
        pass

    def _add_write_sync(self, operation, write_values):
        pass

    def _check_create(self, operation):
        found = False
        creations = [
            element for
            element in self.operations if
            element.model_name == operation.model_name and
            element.record_id == operation.record_id and
            element.record_operation == CREATE_RECORD
        ]
        if creations:
            self._add_create_sync(creations[0])
            found = True
        return found

    def _transform_write(self, operation):
        # if there is a create, ignore write
        if self._check_create(operation):
            return

        # merge all writes
        other_writes = [
            element for
            element in self.operations if
            element.model_name == operation.model_name and
            element.record_id == operation.record_id
        ]

        write_values = cPickle.loads(operation.operation_data)
        for other_write in other_writes:
            other_values = cPickle.loads(other_write.operation_data)
            other_values.update(write_values)
            write_values = other_values

        self._add_write_sync(operation, write_values)

    def _merge_operations(self):
        # operations are already sorted by id
        # for each model_name + record_id, there is only one
        # product operation left after merge:
        # add create directly
        # unlink is always the last for a model_name + record_id
        # for template unlink, ignore all variant unlink operations
        # ignore write if there is a create
        for operation in self.operations:
            source_key = (operation.model_name,
                          operation.record_id)
            if source_key in self.processed:
                continue
            else:
                self.processed.add(source_key)
                if operation.record_operation == CREATE_RECORD:
                    self._add_create_sync(operation)
                elif operation.record_operation == UNLINK_RECORD:
                    self._transform_unlink(operation)
                elif operation.record_operation == WRITE_RECORD:
                    self._transform_write(operation)
                else:
                    message = "Unknown product operation type: {}".format(
                        operation.record_operation)
                    _logger.warning(message)

    def transform(self):
        self._get_operations()
        self._merge_operations()
