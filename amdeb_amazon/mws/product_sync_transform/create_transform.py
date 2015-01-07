# -*- coding: utf-8 -*-

import logging

from .update_transformer import UpdateTransformer
from ...models_access import OdooProductAccess

_logger = logging.getLogger(__name__)


class CreateTransformer(UpdateTransformer):

    def _convert_variation(self, sync_value):
        has_attr = False
        attributes = self._odoo_product.get_attributes(self._product)
        for attr in attributes:
            if attr[0] == 'Color':
                sync_value['Color'] = attr[1]
                has_attr = True
            if attr[0] == 'Size':
                sync_value['Size'] = attr[1]
                has_attr = True
        if not has_attr:
            _logger.warning("No variant attribute found in sync transform.")
            sync_value = None
        return sync_value

    # check the required field
    # create a pseudo-sku for multi-variant template
    def _convert_sync(self, sync_op):
        sync_value = super(CreateTransformer, self)._convert_sync(sync_op)
        # only three creation possibilities:
        # it is a partial variant
        # it is a template: multi-variant or not
        if OdooProductAccess.is_product_variant(self._product):
            # this is an independent variant
            if self._odoo_product.is_partial_variant(sync_op):
                _logger.warning("wrong sync creation for partial variant.")
                sync_value = None
            else:
                sync_value['Parentage'] = 'child'
                sync_value = self._convert_variation(sync_value)
        else:
            if not sync_value.get('Description', None):
                self._raise_exception('Description')

            if OdooProductAccess.has_multi_variants(self._product):
                sync_value['SKU'] = OdooProductAccess.generate_sku(
                    self._product.id)
                sync_value['Parentage'] = 'parent'

        return sync_value
