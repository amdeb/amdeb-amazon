# -*- coding: utf-8 -*-

import logging

from .update_transformer import UpdateTransformer
from ...models_access import OdooProductAccess

_logger = logging.getLogger(__name__)


class CreateTransformer(UpdateTransformer):

    def _convert_variation(self, sync_value):
        has_color = False
        has_size = False
        attributes = OdooProductAccess.get_attributes(self._product)
        for attr in attributes:
            if attr[0] == 'Color':
                sync_value['Color'] = attr[1]
                has_color = True
            if attr[0] == 'Size':
                sync_value['Size'] = attr[1]
                has_size = True

        if has_color and has_size:
            sync_value['VariationTheme'] = 'SizeColor'
        elif has_color:
            sync_value['VariationTheme'] = 'Color'
        elif has_size:
            sync_value['VariationTheme'] = 'Size'
        else:
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
        if OdooProductAccess.product_is_variant(self._product):
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
                sync_value['Parentage'] = 'parent'

        return sync_value
