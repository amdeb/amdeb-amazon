# -*- coding: utf-8 -*-

import logging
from ...models_access import OdooProductAccess, ProductSyncAccess

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

    def _convert_sync(self, sync_op):
        sync_value = {'ID': sync_op.id}
        self._product = self._odoo_product.get_product(sync_op)
        sku = self._odoo_product.get_sku(sync_op)
        BaseTransformer._check_string(sync_value, 'SKU', sku)
        return sync_value

    def transform(self, sync_ops):
        # we change sync_ops record set because its copy
        # creates a new record set that is saved in table
        sync_values = []
        for sync_op in sync_ops:
            try:
                sync_value = self._convert_sync(sync_op)
                if sync_value:
                    sync_values.append(sync_value)
                else:
                    log_template = "Sync id {0} has empty value. Skip it "
                    _logger.debug(log_template.format(sync_op.id))

                    sync_ops = sync_ops - sync_op
                    self._product_sync.update_sync_new_empty_value(sync_op)
            except Exception as ex:
                log_template = "Sync transform error for sync id {0}  " \
                               "Exception: {1}."
                _logger.debug(log_template.format(sync_op.id, ex.message))

                sync_ops = sync_ops - sync_op
                self._product_sync.update_sync_new_exception(sync_op, ex)

        return sync_values
