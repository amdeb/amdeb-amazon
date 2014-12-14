# -*- coding: utf-8 -*-

import cPickle
import logging
_logger = logging.getLogger(__name__)

from ..shared.utility import field_utcnow

from ..shared.model_names import (
    PRODUCT_TEMPLATE_TABLE,
    PRODUCT_PRODUCT_TABLE,
    AMAZON_SYNC_ACTIVE_FIELD,
    AMAZON_CREATION_SUCCESS_FIELD,
    PRODUCT_PRICE_FIELD,
    PRODUCT_AVAILABLE_QUANTITY_FIELD,
    PRODUCT_AMAZON_IMAGE_TRIGGER_FIELD,

    PRODUCT_OPERATION_TABLE,
    MODEL_NAME_FIELD,
    RECORD_ID_FIELD,
    TEMPLATE_ID_FIELD,
    RECORD_OPERATION_FIELD,
    OPERATION_DATA_FIELD,
    AMAZON_SYNC_TIMESTAMP_FIELD,

    AMAZON_PRODUCT_SYNC_TABLE,
    SYNC_TYPE_FIELD,
    SYNC_DATA_FIELD,
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
        self._env = env
        self._new_operations = None
        # this set keeps transformed model_name and record_id
        self._transformed_operations = set()

    def _get_operations(self):
        """
        Get the new operations ordered by descending id (creation time)
        A new operation doesn't have a sync timestamp
        """
        operation_table = self._env[PRODUCT_OPERATION_TABLE]
        search_domain = [
            (AMAZON_SYNC_TIMESTAMP_FIELD, '=', False),
        ]
        self._new_operations = operation_table.search(
            search_domain,
            order="id desc")

    def _set_operation_sync_timestamp(self):
        # set sync timestamp for each operation
        for operation in self._new_operations:
            operation[AMAZON_SYNC_TIMESTAMP_FIELD] = field_utcnow()

    def _get_sync_active(self, operation):
        model = self._env[operation[MODEL_NAME_FIELD]]
        records = model.browse(operation[RECORD_ID_FIELD])
        sync_active = records[0][AMAZON_SYNC_ACTIVE_FIELD]
        created = records[0][AMAZON_CREATION_SUCCESS_FIELD]
        return sync_active, created

    def _insert_sync_record(self, operation, sync_type, sync_data=None):
        """
        Create a sync operation record
        """

        if sync_data:
            sync_data = cPickle.dumps(sync_data, cPickle.HIGHEST_PROTOCOL)
        else:
            sync_data = operation[OPERATION_DATA_FIELD]

        sync_record = {
            MODEL_NAME_FIELD: operation[MODEL_NAME_FIELD],
            RECORD_ID_FIELD: operation[RECORD_ID_FIELD],
            TEMPLATE_ID_FIELD: operation[TEMPLATE_ID_FIELD],
            SYNC_TYPE_FIELD: sync_type,
            SYNC_DATA_FIELD: sync_data,
        }

        amazon_sync_table = self._env[AMAZON_PRODUCT_SYNC_TABLE]
        record = amazon_sync_table.create(sync_record)
        log_template = "Model: {0}, record id: {1}, template id: {2}. " \
                       "sync type: {3}, sync record id {4}."
        _logger.debug(log_template.format(
            sync_record[MODEL_NAME_FIELD],
            sync_record[RECORD_ID_FIELD],
            sync_record[TEMPLATE_ID_FIELD],
            sync_record[SYNC_TYPE_FIELD],
            record.id
        ))

    def _add_create_sync(self, operation):
        (sync_active, _) = self._get_sync_active(operation)
        if sync_active:
            self._insert_sync_record(operation, SYNC_CREATE)
        else:
            log_template = "Amazon Sync is  inactive for create " \
                           "operation. Model: {0}, Record id: {1}"
            _logger.debug(log_template.format(
                operation[MODEL_NAME_FIELD], operation[RECORD_ID_FIELD]
            ))

    def _skip_variant_unlink(self, operation):
        # assume that MWS has cascade delete -- TBD
        # remove all variant operations if this is a template unlink
        if operation[MODEL_NAME_FIELD] == PRODUCT_TEMPLATE_TABLE:
            ignored = [
                (variant[MODEL_NAME_FIELD], variant[RECORD_ID_FIELD]) for
                variant in self._new_operations if
                variant[MODEL_NAME_FIELD] == PRODUCT_PRODUCT_TABLE and
                variant[TEMPLATE_ID_FIELD] == operation[RECORD_ID_FIELD]
            ]
            self._transformed_operations.update(ignored)

    def _transform_unlink(self, operation):
        """
        Unlink a product if it is created in Amazon, even
        its sync active flag is False because
        keeping it in Amazon will cause many confusing when
        we download reports, history etc but couldn't fina
        in locally.
        """
        (_, created) = self._get_sync_active(operation)
        if created:
            self._insert_sync_record(operation, SYNC_DELETE)
        else:
            log_template = "Product is not created in Amazon for unlink " \
                           "operation for Model: {0}, Record id: {1}"
            _logger.debug(log_template.format(
                operation[MODEL_NAME_FIELD], operation[RECORD_ID_FIELD]
            ))

        self._skip_variant_unlink(operation)

    def _check_create(self, operation):
        found = False
        creations = [
            element for
            element in self._new_operations if
            element[MODEL_NAME_FIELD] == operation[MODEL_NAME_FIELD] and
            element[RECORD_ID_FIELD] == operation[RECORD_ID_FIELD] and
            element[RECORD_OPERATION_FIELD] == CREATE_RECORD
        ]
        if creations:
            self._add_create_sync(creations[0])
            found = True
        return found

    def _transform_price(self, operation, write_values):
        price = write_values.pop(PRODUCT_PRICE_FIELD, None)
        if price is not None:
            if price >= 0:
                update_value = {PRODUCT_PRICE_FIELD: price}
                self._insert_sync_record(operation, SYNC_PRICE, update_value)
            else:
                _logger.warning("Price {} is a negative number.".format(
                    price
                ))

    def _transform_inventory(self, operation, write_values):
        qty_available = write_values.pop(
            PRODUCT_AVAILABLE_QUANTITY_FIELD, None)
        if qty_available is not None:
            update_value = {PRODUCT_AVAILABLE_QUANTITY_FIELD: qty_available}
            self._insert_sync_record(operation, SYNC_INVENTORY, update_value)

    def _transform_image(self, operation, write_values):
        image_trigger = write_values.pop(
            PRODUCT_AMAZON_IMAGE_TRIGGER_FIELD, None)
        if image_trigger:
            self._insert_sync_record(operation, SYNC_IMAGE)

            # should reset image trigger
            model = self._env[operation[MODEL_NAME_FIELD]]
            records = model.browse(operation[RECORD_ID_FIELD])
            records.write({PRODUCT_AMAZON_IMAGE_TRIGGER_FIELD: False})

    def _transform_update(self, operation, write_values):
        self._transform_price(operation, write_values)
        self._transform_inventory(operation, write_values)
        self._transform_image(operation, write_values)
        if write_values:
            self._insert_sync_record(operation, SYNC_UPDATE, write_values)

    def _transform_write(self, operation, write_values):
        """transform a write operation to one or more sync operations
        1. If sync active changes, generate create or deactivate sync. Done
        2. If sync active or creation_success is False, ignore all changes.
        Done.
        3. If price, inventory and image change, generate
        corresponding syncs. image triggers is set to False.
        4. If any write values left, generate an update sync
        """
        sync_active_value = write_values.get(AMAZON_SYNC_ACTIVE_FIELD, None)
        (sync_active, created) = self._get_sync_active(operation)
        if sync_active_value is not None:
            if sync_active_value:
                _logger.debug("Amazon sync active changes to "
                              "True, generate a create sync.")
                self._insert_sync_record(operation, SYNC_CREATE)
            else:
                # no need to deactivate it if not created
                if created:
                    _logger.debug("Amazon sync active changes to "
                                  "False, generate a deactivate sync.")
                    self._insert_sync_record(operation, SYNC_DEACTIVATE)
        else:
            if sync_active and created:
                self._transform_update(operation, write_values)
            else:
                _logger.debug("Product write is inactive or is not created "
                              "in Amazon. Ignore it.")

    def _merge_write(self, operation):
        write_values = cPickle.loads(operation[OPERATION_DATA_FIELD])
        log_template = "merge write operation for Model: {0} " \
                       "record id: {1}, template id: {2}, values {3}."
        _logger.debug(log_template.format(
            operation[MODEL_NAME_FIELD],
            operation[RECORD_ID_FIELD],
            operation[TEMPLATE_ID_FIELD],
            write_values
        ))

        # if there is a create operation, ignore write
        if self._check_create(operation):
            _logger.debug("found a create operation, ignore write operation")
            return

        # merge all writes that are ordered by operation id
        other_writes = [
            record for record in self._new_operations if
            record[MODEL_NAME_FIELD] == operation[MODEL_NAME_FIELD] and
            record[RECORD_ID_FIELD] == operation[RECORD_ID_FIELD]
        ]

        for other_write in other_writes:
            other_values = cPickle.loads(other_write[OPERATION_DATA_FIELD])
            other_values.update(write_values)
            write_values = other_values
            _logger.debug("merged write values: {}".format(
                write_values
            ))

        self._transform_write(operation, write_values)

    def _merge_operations(self):
        """
        operations are already sorted by ids in descending order
        for each model_name + record_id, there is only one
        product operation left after merge:
        1. add create directly
        2. unlink is always the last for a model_name + record_id
        for template unlink, ignore all variant unlink operations
        3. ignore write if there is a create
        4. merge all writes into one then break it into different
        sync operations such as update, price, inventory and image
        """
        for operation in self._new_operations:
            record_key = (operation[MODEL_NAME_FIELD],
                          operation[RECORD_ID_FIELD])
            if record_key in self._transformed_operations:
                continue
            else:
                self._transformed_operations.add(record_key)
                record_operation = operation[RECORD_OPERATION_FIELD]
                if record_operation == CREATE_RECORD:
                    self._add_create_sync(operation)
                elif record_operation == UNLINK_RECORD:
                    self._transform_unlink(operation)
                elif record_operation == WRITE_RECORD:
                    self._merge_write(operation)
                else:
                    template = "Invalid product operation type {0} " \
                               "for {1}: {2}"
                    message = template.format(
                        record_operation,
                        operation[MODEL_NAME_FIELD],
                        operation[RECORD_ID_FIELD])
                    _logger.error(message)
                    raise ValueError(message)

    def transform(self):
        """
        get new product operations
        set amazon sync timestamp
        merge/split product operations into sync operations
        """
        self._get_operations()
        self._set_operation_sync_timestamp()
        self._merge_operations()
