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
    SYNC_CREATE,
    # SYNC_UPDATE,
    SYNC_DELETE,
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

    def _get_sync_active(self, operation):
        model = self.env[operation.model_name]
        records = model.browse(operation.record_id)
        return records[0].amazon_sync_active

    def _add_sync_record(self, operation, sync_type):
        sync_record = dict(
            model_name=operation.model_name,
            record_id=operation.record_id,
            template_id=operation.template_id,
            sync_type=sync_type,
            sync_data=operation.operation_data,
        )
        record = self.amazon_sync.create(sync_record)
        logger_template = "Model: {0}, record id: {1}, template id: {2}. " \
                      "sync type: {3}, sync record id {4}."
        _logger.debug(logger_template.format(
            sync_record['model_name'],
            sync_record['record_id'],
            sync_record['template_id'],
            sync_record['sync_type'],
            record.id
        ))


    def _transform_unlink(self, operation):
        sync_active = self._get_sync_active(operation)
        if sync_active:
            self._add_sync_record(operation, SYNC_DELETE)
        else:
            template = "Sync is not active for unlink {0}: {1}"
            _logger.debug(template.format(
                operation.model_name, operation.record_id
            ))

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
        sync_active = self._get_sync_active(operation)
        if sync_active:
            self._add_sync_record(operation, SYNC_CREATE)
        else:
            template = "Sync is not active for create {0}: {1}"
            _logger.debug(template.format(
                operation.model_name, operation.record_id
            ))

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
        write_values = cPickle.loads(operation.operation_data)
        logger_template = "transform write operation for Model: {0} " \
                          "record id: {1}, template id: {2}, values {3}."
        _logger.debug(logger_template.format(
            operation.model_name,
            operation.record_id,
            operation.template_id,
            write_values
        ))

        # if there is a create, ignore write
        if self._check_create(operation):
            _logger.debug("found a create operation, ignore write operation")
            return

        # merge all writes
        other_writes = [
            element for
            element in self.operations if
            element.model_name == operation.model_name and
            element.record_id == operation.record_id
        ]

        for other_write in other_writes:
            other_values = cPickle.loads(other_write.operation_data)
            other_values.update(write_values)
            write_values = other_values
            _logger.debug("merged write values: {}".format(
                write_values
            ))

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
            record_key = (operation.model_name, operation.record_id)
            if record_key in self.processed:
                continue
            else:
                self.processed.add(record_key)
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
