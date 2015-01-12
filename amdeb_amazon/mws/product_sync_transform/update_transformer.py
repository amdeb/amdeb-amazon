# -*- coding: utf-8 -*-

import logging
from ...shared.model_names import (
    MODEL_NAME_FIELD, RECORD_ID_FIELD,
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

_logger = logging.getLogger(__name__)


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

    def _merge_others(self, sync_op, sync_ops):
        """
        Override the parent method to merge write field names
        """
        _logger.debug("About to merge other update syncs.")
        merged_fields = ProductSyncAccess.get_write_field_names(sync_op)
        _logger.debug("initial write fields: {}.".format(merged_fields))
        other_writes = [
            record for record in sync_ops if
            record[MODEL_NAME_FIELD] == sync_op[MODEL_NAME_FIELD] and
            record[RECORD_ID_FIELD] == sync_op[RECORD_ID_FIELD] and
            record.id != sync_op.id
        ]

        is_merged = False
        for other_write in other_writes:
            other_values = ProductSyncAccess.get_write_field_names(
                other_write)
            merged_fields = merged_fields.union(other_values)
            _logger.debug("Merged write fields: {}".format(merged_fields))
            is_merged = True

        if is_merged:
            ProductSyncAccess.save_write_field_names(sync_op, merged_fields)
        else:
            _logger.debug("No other update syncs to merge.")
