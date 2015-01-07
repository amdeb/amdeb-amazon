# -*- coding: utf-8 -*-

# import cPickle
import logging

from ...shared.model_names import (
    PRODUCT_NAME_FIELD,
    PRODUCT_DESCRIPTION_SALE_FIELD,
    PRODUCT_AMAZON_DESCRIPTION_FIELD,
    PRODUCT_PRODUCT_BRAND_FIELD,
    PRODUCT_BULLET_POINT_PREFIX,
    PRODUCT_BULLET_POINT_COUNT,
)
from .base_transfomer import BaseTransformer

_logger = logging.getLogger(__name__)


class UpdateTransformer(BaseTransformer):
    """
    This class transform update values to update message fields
    """
    def _convert_bullet_points(self):
        bullet_points = []
        for index in range(1, 1 + PRODUCT_BULLET_POINT_COUNT):
            name = PRODUCT_BULLET_POINT_PREFIX + str(index)
            bullet = self._product[name]
            if bullet:
                bullet = bullet.strip()
                if bullet:
                    bullet_points.append(bullet)
        return bullet_points

    def _convert_sync(self, sync_op):
        # This method is also shared by create transform

        sync_value = super(UpdateTransformer, self)._convert_sync(sync_op)

        sync_value['Title'] = self._check_string(
            'Title', self._product[PRODUCT_NAME_FIELD])

        description = self._product[PRODUCT_AMAZON_DESCRIPTION_FIELD]
        if not description:
            description = self._product[PRODUCT_DESCRIPTION_SALE_FIELD]
        self._add_string(sync_value, 'Description', description)

        self._add_string(sync_value, 'Brand',
                         self._product[PRODUCT_PRODUCT_BRAND_FIELD])

        bullet_points = self._convert_bullet_points()
        if bullet_points:
            sync_value['BulletPoint'] = bullet_points
        return sync_value
