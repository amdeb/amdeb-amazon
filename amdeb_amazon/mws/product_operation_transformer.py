# -*- coding: utf-8 -*-

import cPickle
import logging
_logger = logging.getLogger(__name__)

from ..shared.model_names import (
    # common fields
    MODEL_NAME_FIELD,
    RECORD_ID_FIELD,

    PRODUCT_TEMPLATE_TABLE,
    PRODUCT_VARIANT_COUNT_FIELD,

    PRODUCT_PRODUCT_TABLE,
    AMAZON_SYNC_ACTIVE_FIELD,
    PRODUCT_PRICE_FIELD,
    PRODUCT_AVAILABLE_QUANTITY_FIELD,
    PRODUCT_AMAZON_IMAGE_TRIGGER_FIELD,

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

from .product_sync_creation import ProductSyncCreation
from .amazon_product_access import AmazonProductAccess


class ProductOperationTransformer(object):
    """
    Transform product operations into sync operations
    A product may be unlinked in Odoo -- be careful to check
    """
    def __init__(self, env, new_operations):
        self._env = env
        self._sync_creation = ProductSyncCreation(env)
        self._new_operations = new_operations
        # this set keeps transformed model_name and record_id
        self._transformed_operations = set()
        self._amazon_product_access = AmazonProductAccess(env)

    def _get_sync_active(self, operation):
        model = self._env[operation[MODEL_NAME_FIELD]]
        record = model.browse(operation[RECORD_ID_FIELD])
        sync_active = record[AMAZON_SYNC_ACTIVE_FIELD]
        return sync_active

    def _has_multi_variants(self, operation):
        # don't insert create sync if it is the only variant
        result = False
        template = self._env[PRODUCT_TEMPLATE_TABLE]
        record = template.browse(operation[TEMPLATE_ID_FIELD])
        if record[PRODUCT_VARIANT_COUNT_FIELD] > 1:
            result = True
        return result

    def _add_create_sync(self, operation):
        # ignore variant creation if it is the only variant
        model_name = operation[MODEL_NAME_FIELD]
        if model_name == PRODUCT_PRODUCT_TABLE:
            if not self._has_multi_variants(operation):
                log_template = "Skip single variant creation " \
                               "operation. Model: {0}, Record id: {1}"
                _logger.debug(log_template.format(
                    operation[MODEL_NAME_FIELD], operation[RECORD_ID_FIELD]
                ))
                return

        sync_active = self._get_sync_active(operation)
        if sync_active:
            self._sync_creation.insert_create(operation)
        else:
            log_template = "Amazon Sync is inactive for create " \
                           "operation. Model: {0}, Record id: {1}"
            _logger.debug(log_template.format(
                operation[MODEL_NAME_FIELD], operation[RECORD_ID_FIELD]
            ))

    def _skip_variant_unlink(self, operation):
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
        we download reports, history etc but couldn't find
        it locally.
        """
        # ToDo: should fix unlink for templates with multiple variants
        amazon_product = self._amazon_product_access.get_amazon_product(
            operation)
        if amazon_product:
            self._sync_creation.insert_operation_delete(operation)
            amazon_product.unlink()
        else:
            log_template = "Product is not created in Amazon for unlink " \
                           "operation for Model: {0}, Record id: {1}"
            _logger.debug(log_template.format(
                operation[MODEL_NAME_FIELD], operation[RECORD_ID_FIELD]
            ))

        self._skip_variant_unlink(operation)

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

    def _transform_price(self, operation, write_values):
        price = write_values.pop(PRODUCT_PRICE_FIELD, None)
        if price is not None:
            self._sync_creation.insert_price(operation, price)

    def _transform_inventory(self, operation, write_values):
        inventory = write_values.pop(PRODUCT_AVAILABLE_QUANTITY_FIELD, None)
        if inventory is not None:
            self._sync_creation.insert_inventory(operation, inventory)

    def _transform_image(self, operation, write_values):
        image_trigger = write_values.pop(
            PRODUCT_AMAZON_IMAGE_TRIGGER_FIELD, None)
        # create image sync regardless the image_trigger value
        if image_trigger is not None:
            self._sync_creation.insert_image(operation)

    def _transform_update(self, operation, write_values):
        self._transform_price(operation, write_values)
        self._transform_inventory(operation, write_values)
        self._transform_image(operation, write_values)
        if write_values:
            self._sync_creation.insert_update(operation, write_values)

    def _convert_write(self, operation, write_values):
        """transform a write operation to one or more sync operations
        1. If sync active changes, generate create or deactivate sync. Done
        2. If sync active or creation_success is False, ignore all changes.
        Done.
        3. If price, inventory and image change, generate
        corresponding syncs. image triggers is set to False.
        4. If any write values left, generate an update sync
        """
        sync_active_value = write_values.get(AMAZON_SYNC_ACTIVE_FIELD, None)
        sync_active = self._get_sync_active(operation)
        is_created = self._amazon_product_access.is_created(operation)
        if sync_active_value is not None:
            if sync_active_value:
                _logger.debug("Amazon sync active changes to "
                              "True, generate a create sync.")
                self._sync_creation.insert_create(operation)
            else:
                # no need to deactivate it if not created
                if is_created:
                    _logger.debug("Amazon sync active changes to "
                                  "False, generate a deactivate sync.")
                    self._sync_creation.insert_deactivate(operation)
        else:
            if sync_active and is_created:
                self._transform_update(operation, write_values)
            else:
                _logger.debug("Product write is inactive or is not created "
                              "in Amazon. Ignore it.")

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
            self._add_create_sync(creation)
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
        self._convert_write(operation, merged_values)

    def transform(self):
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
                operation_type = operation[OPERATION_TYPE_FIELD]
                if operation_type == CREATE_RECORD:
                    self._add_create_sync(operation)
                elif operation_type == UNLINK_RECORD:
                    self._transform_unlink(operation)
                elif operation_type == WRITE_RECORD:
                    self._transform_write(operation)
                else:
                    template = "Invalid product operation type {0} " \
                               "for {1}: {2}"
                    message = template.format(
                        operation_type,
                        operation[MODEL_NAME_FIELD],
                        operation[RECORD_ID_FIELD])
                    _logger.error(message)
                    raise ValueError(message)
