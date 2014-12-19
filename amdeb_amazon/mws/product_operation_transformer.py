# -*- coding: utf-8 -*-

import cPickle
import logging
_logger = logging.getLogger(__name__)

from ..shared.model_names import (
    # product fields
    MODEL_NAME_FIELD,
    RECORD_ID_FIELD,
    AMAZON_SYNC_ACTIVE_FIELD,

    # product operation fields
    TEMPLATE_ID_FIELD,
    OPERATION_TYPE_FIELD,
    OPERATION_DATA_FIELD,
)

from ..shared.db_operation_types import (
    CREATE_RECORD,
    WRITE_RECORD,
    UNLINK_RECORD,
)

from .product_unlink_tranformer import ProductUnlinkTransformer
from .product_create_transformer import ProductCreateTransformer
from .product_write_transformer import ProductWriteTransformer
from .product_utility import ProductUtility


class ProductOperationTransformer(object):
    """
    Transform product operations into sync operations
    A product may be unlinked in Odoo -- be careful to check
    """
    def __init__(self, env, new_operations):
        self._env = env
        self._new_operations = new_operations

        self._unlink_transformer = ProductUnlinkTransformer(
            env, new_operations)
        self._create_transformer = ProductCreateTransformer(env)
        self._writer_transformer = ProductWriteTransformer(env)

        self._utility = ProductUtility(env)

        # this set keeps transformed model_name and record_id
        self._transformed_operations = set()

    def _get_sync_active(self, operation):
        model = self._env[operation[MODEL_NAME_FIELD]]
        record = model.browse(operation[RECORD_ID_FIELD])
        sync_active = record[AMAZON_SYNC_ACTIVE_FIELD]
        return sync_active

    def _check_create(self, operation):
        found = None
        creations = [
            element for
            element in self._new_operations if
            element[MODEL_NAME_FIELD] == operation[MODEL_NAME_FIELD] and
            element[RECORD_ID_FIELD] == operation[RECORD_ID_FIELD] and
            element[OPERATION_TYPE_FIELD] == CREATE_RECORD
        ]
        if creations:
            found = creations[0]
        return found

    def _merge_write(self, operation, write_values):
        # merge all writes that are ordered by operation id
        merged_values = write_values
        other_writes = [
            record for record in self._new_operations if
            record[MODEL_NAME_FIELD] == operation[MODEL_NAME_FIELD] and
            record[RECORD_ID_FIELD] == operation[RECORD_ID_FIELD] and
            record.id != operation.id
        ]

        for other_write in other_writes:
            other_values = cPickle.loads(other_write[OPERATION_DATA_FIELD])
            other_values.update(merged_values)
            merged_values = other_values
            _logger.debug("merged write values: {}".format(merged_values))
        return merged_values

    def _transform_write(self, operation):
        # if there is a create operation, ignore write
        creation = self._check_create(operation)
        if creation:
            self._create_transformer.transform(creation)
            _logger.debug("found a create operation, ignore write operation")
            return

        write_values = cPickle.loads(operation[OPERATION_DATA_FIELD])
        log_template = "transform write operation for Model: {0} " \
                       "record id: {1}, template id: {2}, values {3}."
        _logger.debug(log_template.format(
            operation[MODEL_NAME_FIELD],
            operation[RECORD_ID_FIELD],
            operation[TEMPLATE_ID_FIELD],
            write_values
        ))
        merged_values = self._merge_write(operation, write_values)
        sync_active = self._get_sync_active(operation)
        self._writer_transformer.transform(
            operation, merged_values, sync_active)

    def _transform_create_write(self, operation):
        operation_type = operation[OPERATION_TYPE_FIELD]
        # for existed product create or write operation
        if operation_type == CREATE_RECORD:
            if self._get_sync_active(operation):
                self._create_transformer.transform(operation)
            else:
                log_template = "Amazon Sync is inactive for create " \
                               "operation. Model: {0}, Record id: {1}"
                _logger.debug(log_template.format(
                    operation[MODEL_NAME_FIELD],
                    operation[RECORD_ID_FIELD]
                ))
        elif operation_type == WRITE_RECORD:
            self._transform_write(operation)
        else:
            template = "Invalid product operation type {0} " \
                       "for {1}: {2}"
            _logger.error(template.format(
                operation_type,
                operation[MODEL_NAME_FIELD],
                operation[RECORD_ID_FIELD]
            ))

    def _transform_operation(self, operation):
        operation_type = operation[OPERATION_TYPE_FIELD]
        if operation_type == UNLINK_RECORD:
            self._unlink_transformer.transform(operation)
        elif not self._utility.is_existed(operation):
            log_template = "Ignore operation for unlinked " \
                           "Model: {0}, Record id: {1}"
            _logger.debug(log_template.format(
                operation[MODEL_NAME_FIELD],
                operation[RECORD_ID_FIELD]
            ))
        else:
            # create or write for existing product
            self._transform_create_write(operation)

    def transform(self):
        """
        operations are already sorted by ids in descending order
        for each model_name + record_id, there is only one
        product operation left after merge:
        1. add create directly
        2. unlink is always the last for a model_name + record_id
        for template unlink -- it will be transformed first !!!
        3. ignore write if there is a create
        4. merge all writes into one then break it into different
        sync operations such as update, price, inventory and image
        """
        _logger.debug("Transforming new product operations.")
        for operation in self._new_operations:
            record_key = (operation[MODEL_NAME_FIELD],
                          operation[RECORD_ID_FIELD])
            if record_key in self._transformed_operations:
                continue
            else:
                self._transformed_operations.add(record_key)
                self._transform_operation(operation)