# -*- coding: utf-8 -*-

import logging

from ...models_access import OdooProductAccess
from ...model_names.shared_names import SHARED_NAME_FIELD
from ...model_names.product_template import (
    PRODUCT_AMAZON_DESCRIPTION_FIELD,
    PRODUCT_PRODUCT_BRAND_FIELD,
)
from ...model_names.product_attribute import (
    PRODUCT_ATTRIBUTE_COLOR_VALUE,
    PRODUCT_ATTRIBUTE_SIZE_VALUE,
)
from .base_transfomer import BaseTransformer

_logger = logging.getLogger(__name__)


class CreateTransformer(BaseTransformer):
    def _convert_description(self, sync_value):
        title = self._product[SHARED_NAME_FIELD]
        self._check_string(sync_value, 'Title', title)

        description = self._product[PRODUCT_AMAZON_DESCRIPTION_FIELD]
        self._check_string(sync_value, 'Description', description)

        # Todo: required fields
        sync_value['Department'] = "womens"
        sync_value['ItemType'] = 'handbags'

        brand = self._product[PRODUCT_PRODUCT_BRAND_FIELD]
        self._check_string(sync_value, 'Brand', brand)

        bullet_points = OdooProductAccess.get_bullet_points(self._product)
        if bullet_points:
            sync_value['BulletPoint'] = bullet_points

        sync_value['Department'] = "womens"
        sync_value['ItemType'] = 'handbags'

    def _convert_variation(self, sync_value):
        has_attribute = False
        attributes = OdooProductAccess.get_variant_attributes(self._product)
        for attr in attributes:
            if attr[0] == PRODUCT_ATTRIBUTE_COLOR_VALUE:
                sync_value[PRODUCT_ATTRIBUTE_COLOR_VALUE] = attr[1]
                has_attribute = True
            if attr[0] == PRODUCT_ATTRIBUTE_SIZE_VALUE:
                sync_value[PRODUCT_ATTRIBUTE_SIZE_VALUE] = attr[1]
                has_attribute = True

        if not has_attribute:
            _logger.warning("No variant attribute found in sync transform.")
            sync_value = None
        return sync_value

    def _get_variant_theme(self, sync_value):
        attr_names = OdooProductAccess.get_template_attribute_names(
            self._product
        )

        has_color = PRODUCT_ATTRIBUTE_COLOR_VALUE in attr_names
        has_size = PRODUCT_ATTRIBUTE_SIZE_VALUE in attr_names
        if has_color and has_size:
            sync_value['VariationTheme'] = 'SizeColor'
        elif has_color:
            sync_value['VariationTheme'] = PRODUCT_ATTRIBUTE_COLOR_VALUE
        elif has_size:
            sync_value['VariationTheme'] = PRODUCT_ATTRIBUTE_SIZE_VALUE
        else:
            _logger.warning("No variant attribute found for multi-variant "
                            "template. Skip sync transform.")
            sync_value = None

        return sync_value

    def _convert_sync(self, sync_op):
        sync_value = super(CreateTransformer, self)._convert_sync(sync_op)
        self._convert_description(sync_value)
        # only three creation possibilities 1) a non-partial variant
        # 2) a multi-variant template 3) a single-variant template
        if OdooProductAccess.is_product_variant(self._product):
            # this is an independent variant
            sync_value['Parentage'] = 'child'
            sync_value = self._convert_variation(sync_value)
        else:
            if 'Description' not in sync_value:
                self._raise_exception('Description')

            if OdooProductAccess.is_multi_variant_template(self._product):
                sync_value['Parentage'] = 'parent'
                sync_value = self._get_variant_theme(sync_value)

        return sync_value
