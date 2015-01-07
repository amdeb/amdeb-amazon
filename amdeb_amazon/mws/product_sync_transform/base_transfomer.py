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

    def _check_string(self, sync_value, field_name, field_value):
        if field_value:
            field_value = field_value.strip()
            if field_value:
                sync_value[field_name] = field_value
        self._raise_exception(field_name)

    @staticmethod
    def _add_string(sync_value, field_name, field_value):
        if field_value:
            field_value = field_value.strip()
            if field_value:
                sync_value[field_name] = field_value

    def _convert_sync(self, sync_op):
        sync_value = {'ID': sync_op.id}
        self._product = self._odoo_product.browse(sync_op)
        sku = self._odoo_product.get_sku(sync_op)
        self._check_string(sync_value, 'SKU', sku)
        return sync_value

    def transform(self, sync_ops):
        sync_values = []
        valid_ops = []
        for sync_op in sync_ops:
            try:
                sync_value = self._convert_sync(sync_op)
                if sync_value:
                    sync_values.append(sync_value)
                    valid_ops.append(sync_op)
                else:
                    self._product_sync.update_sync_new_empty_value(sync_op)
            except Exception as ex:
                log_template = "Sync transform error {0} for sync id {1}."
                _logger.debug(log_template.format(sync_op.id, ex.message))
                self._product_sync.update_sync_new_exception(sync_op, ex)

        return valid_ops, sync_values
