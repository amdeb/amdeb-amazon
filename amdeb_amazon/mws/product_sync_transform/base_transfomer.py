# -*- coding: utf-8 -*-

import logging
from ...models_access import OdooProductAccess, ProductSyncAccess
from ...shared.model_names import (
    MODEL_NAME_FIELD, RECORD_ID_FIELD,
    SYNC_TYPE_FIELD,
)
from ...shared.sync_operation_types import SYNC_DELETE

_logger = logging.getLogger(__name__)


class BaseTransformer(object):
    """
    This is the base transform
    """
    def __init__(self, env):
        self._odoo_product = OdooProductAccess(env)
        self._product_sync = ProductSyncAccess(env)
        self._product = None

    @staticmethod
    def _raise_exception(field_name):
        template = "Invalid {} value in Sync transformation"
        raise ValueError(template.format(field_name))

    @staticmethod
    def _check_string(sync_value, field_name, field_value):
        # add field to sync value, raise an exception if the value is invalid
        if field_value:
            field_value = field_value.strip()
            if field_value:
                sync_value[field_name] = field_value
                return

        # otherwise raise an exception for required field
        BaseTransformer._raise_exception(field_name)

    @staticmethod
    def _add_string(sync_value, field_name, field_value):
        # add valid field value to sync value
        if field_value:
            field_value = field_value.strip()
            if field_value:
                sync_value[field_name] = field_value

    @staticmethod
    def _remove_syncs(sync_ops, removing_ops):
        for sync_op in removing_ops:
            sync_ops = sync_ops - sync_op
        return sync_ops

    def _merge_others(self, sync_op, sync_ops):
        """
        This is stub that to be implement in a child class if
        it needs to do other work
        """
        pass

    # the default implementation, update transform should combine values
    def _check_redundant(self, sync_ops):
        _logger("check and remove redundant syncs.")
        processed = set()
        redundant = []
        for sync_op in sync_ops:
            op_key = (sync_op[MODEL_NAME_FIELD], sync_op[RECORD_ID_FIELD])
            if op_key in processed:
                self._product_sync.set_sync_redundant(sync_op)
                redundant.append(sync_op)
            else:
                processed.add(op_key)
                # a hook method that might be implemented in a subclass
                self._merge_others(sync_op, sync_ops)

        _logger("Found {} redundant syncs.".format(len(redundant)))
        return BaseTransformer._remove_syncs(sync_ops, redundant)

    def _convert_sync(self, sync_op):
        """
        To be called and extended in subclass to convert more fields
        """
        sync_value = {'ID': sync_op.id}
        sku = self._odoo_product.get_sku(sync_op)
        BaseTransformer._check_string(sync_value, 'SKU', sku)
        return sync_value

    def _transform_op(self, sync_op, invalid_ops, sync_values):
        self._product = self._odoo_product.get_existed_product(sync_op)

        # for all but delete, we want to make sure the product
        # is not unlinked because of waiting syncs
        if sync_op[SYNC_TYPE_FIELD] != SYNC_DELETE:
            if self._product and self._odoo_product.is_sync_active_product(
                    self._product):
                sync_value = self._convert_sync(sync_op)
                if sync_value:
                    sync_values.append(sync_value)
                else:
                    log_template = "Sync id {0} has empty value. Skip it."
                    _logger.debug(log_template.format(sync_op.id))
                    ProductSyncAccess.update_sync_new_empty_value(sync_op)
                    invalid_ops.append(sync_op)
            else:
                log_template = "Product not found or sync disabled " \
                               "for sync id {0}. Skip it."
                _logger.debug(log_template.format(sync_op.id))
                ProductSyncAccess.set_sync_no_product(sync_op)
                invalid_ops.append(sync_op)

    def transform(self, sync_ops):
        # we change sync_ops record set because making a copy
        # creates a new record set that is saved in table.
        sync_ops = self._check_redundant(sync_ops)

        sync_values = []
        invalid_ops = []
        for sync_op in sync_ops:
            try:
                self._transform_op(sync_op, invalid_ops, sync_values)
            except Exception as ex:
                log_template = "Sync transform error for sync id {0}  " \
                               "Exception: {1}."
                _logger.debug(log_template.format(sync_op.id, ex.message))

                ProductSyncAccess.update_sync_new_exception(sync_op, ex)
                invalid_ops.append(sync_op)

        sync_ops = BaseTransformer._remove_syncs(sync_ops, invalid_ops)

        assert(len(sync_ops) == len(sync_values))
        return sync_ops, sync_values
