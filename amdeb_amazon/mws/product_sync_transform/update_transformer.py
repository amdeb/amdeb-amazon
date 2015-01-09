# -*- coding: utf-8 -*-

from ...shared.model_names import (
    PRODUCT_NAME_FIELD,
    PRODUCT_DESCRIPTION_SALE_FIELD,
    PRODUCT_AMAZON_DESCRIPTION_FIELD,
    PRODUCT_PRODUCT_BRAND_FIELD,
    PRODUCT_BULLET_POINT_PREFIX,
    PRODUCT_BULLET_POINT_COUNT,
)
from .base_transfomer import BaseTransformer
from ...models_access import OdooProductAccess
from ...models_access import ProductSyncAccess


class UpdateTransformer(BaseTransformer):
    """
    This class transform update values to update message fields
    """
    def _check_bullet_points(self, write_field_names, sync_value):
        # the bullet points are changed together
        is_changed = False
        for index in range(1, 1 + PRODUCT_BULLET_POINT_COUNT):
            name = PRODUCT_BULLET_POINT_PREFIX + str(index)
            if name in write_field_names:
                is_changed = True
                break

        if is_changed:
            bullet_points = OdooProductAccess.get_bullet_points(self._product)
            if bullet_points:
                self._has_mws_data = True
                sync_value['BulletPoint'] = bullet_points

    def _convert_description(self, write_field_names, sync_value):
        description = None
        if PRODUCT_AMAZON_DESCRIPTION_FIELD in write_field_names:
            description = self._product[PRODUCT_AMAZON_DESCRIPTION_FIELD]
        elif PRODUCT_DESCRIPTION_SALE_FIELD in write_field_names:
            description = self._product[PRODUCT_DESCRIPTION_SALE_FIELD]

        if description:
            self._has_mws_data = True
            self._add_string(sync_value, 'Description', description)

    def _convert_title(self, write_field_names, sync_value):
        if PRODUCT_NAME_FIELD in write_field_names:
            self._has_mws_data = True
        title = self._product[PRODUCT_NAME_FIELD]
        self._check_string(sync_value, 'Title', title)

    def _convert_brand(self, write_field_names, sync_value):
        if PRODUCT_PRODUCT_BRAND_FIELD in write_field_names:
            brand = self._product[PRODUCT_PRODUCT_BRAND_FIELD]
            if brand:
                self._has_mws_data = True
                self._add_string(sync_value, 'Brand', brand)

    def _convert_sync(self, sync_op):
        # we skip update that doesn't have data to be synced to Amazon
        self._has_mws_data = False

        # we use the most current product data in sync
        sync_value = super(UpdateTransformer, self)._convert_sync(sync_op)
        write_field_names = ProductSyncAccess.get_write_field_names(sync_op)
        if write_field_names:
            self._convert_title(write_field_names, sync_value)
            self._convert_description(write_field_names, sync_value)
            self._convert_brand(write_field_names, sync_value)
            self._check_bullet_points(write_field_names, sync_value)
        else:
            sync_value = None

        if not self._has_mws_data:
            sync_value = None

        return sync_value
