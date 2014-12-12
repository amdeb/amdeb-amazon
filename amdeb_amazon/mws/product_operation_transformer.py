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
)
from ..shared.sync_operation_types import (
    SYNC_CREATE,
    SYNC_UPDATE,
    SYNC_DELETE,
    SYNC_PRICE,
    SYNC_INVENTORY,
    SYNC_IMAGE,
    SYNC_DEACTIVATE,
)
from ..shared.utility import field_utcnow
from ..shared.db_operation_types import (
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

    Methods in this class should not throw exceptions.
    It sets product operation sync timestamp and
    reset image trigger. These changes should be saved
    regardless of sync operation results
    """

    def __init__(self, env):
        self.env = env
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

    def _set_operation_sync_timestamp(self):
        # set sync timestamp for each operation
        for operation in self.operations:
            operation[AMAZON_SYNC_TIMESTAMP_FIELD] = field_utcnow()

    def _get_sync_active(self, operation):
        model = self.env[operation.model_name]
        records = model.browse(operation.record_id)
        sync_active = records[0].amazon_sync_active
        created = records[0].amazon_creation_success
        return sync_active, created

    def _add_sync_record(self, operation, sync_type, sync_data=None):
        """Create a sync operation record"""
        if sync_data:
            sync_data = cPickle.dumps(sync_data, cPickle.HIGHEST_PROTOCOL)
        else:
            sync_data = operation.operation_data

        sync_record = dict(
            model_name=operation.model_name,
            record_id=operation.record_id,
            template_id=operation.template_id,
            sync_type=sync_type,
            sync_data=sync_data,
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
        # there is no reason to not delete it in Amazon
        (_, created) = self._get_sync_active(operation)
        if created:
            self._add_sync_record(operation, SYNC_DELETE)
        else:
            template = "Sync is inactive for unlink operation {0}: {1}"
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
        (sync_active, _) = self._get_sync_active(operation)
        if sync_active:
            self._add_sync_record(operation, SYNC_CREATE)
        else:
            template = "Sync is not active for create operation {0}: {1}"
            _logger.debug(template.format(
                operation.model_name, operation.record_id
            ))

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

    def _transform_price(self, operation, write_values):
        price = write_values.pop('price', None)
        if price is not None:
            if price > 0:
                update_value = dict(price=price)
                self._add_sync_record(operation, SYNC_PRICE, update_value)
            else:
                _logger.warning("Price is not a positive number: {}".format(
                    price
                ))

    def _transform_inventory(self, operation, write_values):
        qty_available = write_values.pop('qty_available', None)
        if qty_available is not None:
            update_value = dict(qty_available=qty_available)
            self._add_sync_record(operation, SYNC_INVENTORY, update_value)

    def _transform_image(self, operation, write_values):
        image_trigger = write_values.pop('amazon_image_trigger', None)
        if image_trigger:
            self._add_sync_record(operation, SYNC_IMAGE)

            # should reset image trigger
            model = self.env[operation.model_name]
            records = model.browse(operation.record_id)
            records.amazon_image_trigger = False

    def _transform_update(self, operation, write_values):
        self._transform_price(operation, write_values)
        self._transform_inventory(operation, write_values)
        self._transform_image(operation, write_values)
        if write_values:
            self._add_sync_record(operation, SYNC_UPDATE, write_values)

    def _transform_write(self, operation, write_values):
        """transform a write operation to one or more sync operations
        1. If sync active changes, generate create or deactivate sync. Done
        2. If sync active or creation_success is False, ignore all changes.
        Done.
        3. If price, inventory and image change, generate
        corresponding syncs. image triggers is set to False.
        4. If any write values left, generate an update sync
        """
        sync_active = write_values.get('amazon_sync_active', None)
        if sync_active is not None:
            _logger.debug("Amazon sync active changed, generate a sync.")
            if sync_active:
                self._add_sync_record(operation, SYNC_CREATE)
            else:
                self._add_sync_record(operation, SYNC_DEACTIVATE)
            return

        (sync_active, created) = self._get_sync_active(operation)
        if not sync_active or not created:
            _logger.debug("Sync is inactive or is not created in Amazon.")
            return

        self._transform_update(operation, write_values)

    def _merge_write(self, operation):
        write_values = cPickle.loads(operation.operation_data)
        logger_template = "transform write operation for Model: {0} " \
                          "record id: {1}, template id: {2}, values {3}."
        _logger.debug(logger_template.format(
            operation.model_name,
            operation.record_id,
            operation.template_id,
            write_values
        ))

        # if there is a create operation, ignore write
        if self._check_create(operation):
            _logger.debug("found a create operation, ignore write operation")
            return

        # merge all writes that are ordered by operation id
        other_writes = [
            element for element in self.operations if
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

        self._transform_write(operation, write_values)

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
                    self._merge_write(operation)
                else:
                    template = "Unknown operation type {0} for {1}: {2}"
                    message = template.format(
                        operation.record_operation,
                        operation.model_name,
                        operation.record_id)
                    _logger.warning(message)
                    raise ValueError(message)

    def transform(self):
        self._get_operations()
        self._set_operation_sync_timestamp()
        self._merge_operations()
