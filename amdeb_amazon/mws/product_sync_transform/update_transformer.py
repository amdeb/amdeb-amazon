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
    def _check_bullet_points(self, sync_data, sync_value):
        # the bullet points are changed together
        is_changed = False
        for index in range(1, 1 + PRODUCT_BULLET_POINT_COUNT):
            name = PRODUCT_BULLET_POINT_PREFIX + str(index)
            if name in sync_data:
                is_changed = True
                break

        if is_changed:
            bullet_points = OdooProductAccess.get_bullet_points(self._product)
            if bullet_points:
                sync_value['BulletPoint'] = bullet_points

    def _convert_description(self, sync_data, sync_value):
        description = None
        if PRODUCT_AMAZON_DESCRIPTION_FIELD in sync_data:
            description = self._product[PRODUCT_AMAZON_DESCRIPTION_FIELD]
        elif PRODUCT_DESCRIPTION_SALE_FIELD in sync_data:
            description = self._product[PRODUCT_DESCRIPTION_SALE_FIELD]
        self._add_string(sync_value, 'Description', description)

    def _convert_sync(self, sync_op):
        # we use the most current product data in sync
        sync_value = super(UpdateTransformer, self)._convert_sync(sync_op)
        sync_data = ProductSyncAccess.get_sync_data(sync_op)
        if sync_data:
            title = self._product[PRODUCT_NAME_FIELD]
            self._check_string(sync_value, 'Title', title)

            self._convert_description(sync_data, sync_value)

            if PRODUCT_PRODUCT_BRAND_FIELD in sync_data:
                brand = self._product[PRODUCT_PRODUCT_BRAND_FIELD]
                self._add_string(sync_value, 'Brand', brand)

            self._check_bullet_points(sync_data, sync_value)
        else:
            sync_value = None

        return sync_value
