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
from ..amazon_names import (
    AMAZON_TITLE_FIELD, AMAZON_ITEM_TYPE_FIELD,
    AMAZON_DEPARTMENT_FIELD, AMAZON_BULLET_POINT_FIELD,
    AMAZON_VARIATION_THEME, AMAZON_DESCRIPTION_FIELD,
    AMAZON_PARENTAGE_FIELD, AMAZON_BRAND_FIELD,
    AMAZON_PARENTAGE_PARENT_VALUE, AMAZON_PARENTAGE_CHILD_VALUE,
)
from .base_transfomer import BaseTransformer

_logger = logging.getLogger(__name__)


class CreateTransformer(BaseTransformer):
    def _convert_description(self, sync_value):
        title = self._product[SHARED_NAME_FIELD]
        self._check_string(sync_value, AMAZON_TITLE_FIELD, title)

        description = self._product[PRODUCT_AMAZON_DESCRIPTION_FIELD]
        self._check_string(sync_value, 'Description', description)

        # Todo: required fields
        sync_value[AMAZON_DEPARTMENT_FIELD] = "womens"
        sync_value[AMAZON_ITEM_TYPE_FIELD] = 'handbags'

        brand = self._product[PRODUCT_PRODUCT_BRAND_FIELD]
        self._check_string(sync_value, AMAZON_BRAND_FIELD, brand)

        bullet_points = OdooProductAccess.get_bullet_points(self._product)
        if bullet_points:
            sync_value[AMAZON_BULLET_POINT_FIELD] = bullet_points

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
            sync_value[AMAZON_VARIATION_THEME] = 'SizeColor'
        elif has_color:
            sync_value[AMAZON_VARIATION_THEME] = PRODUCT_ATTRIBUTE_COLOR_VALUE
        elif has_size:
            sync_value[AMAZON_VARIATION_THEME] = PRODUCT_ATTRIBUTE_SIZE_VALUE
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
            sync_value[AMAZON_PARENTAGE_FIELD] = AMAZON_PARENTAGE_CHILD_VALUE
            sync_value = self._convert_variation(sync_value)
        else:
            if AMAZON_DESCRIPTION_FIELD not in sync_value:
                self._raise_exception(AMAZON_DESCRIPTION_FIELD)

            if OdooProductAccess.is_multi_variant_template(self._product):
                sync_value[AMAZON_PARENTAGE_FIELD] = (
                    AMAZON_PARENTAGE_PARENT_VALUE)
                sync_value = self._get_variant_theme(sync_value)

        return sync_value
