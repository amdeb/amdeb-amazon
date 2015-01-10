# -*- coding: utf-8 -*-

from ..shared.model_names import(
    MODEL_NAME_FIELD, RECORD_ID_FIELD,
    PRODUCT_IS_PRODUCT_VARIANT_FIELD,
    PRODUCT_ATTRIBUTE_VALUE_IDS_FIELD, AMAZON_SYNC_ACTIVE_FIELD,
    PRODUCT_DEFAULT_CODE_FIELD, PRODUCT_VARIANT_COUNT_FIELD,
    PRODUCT_NAME_FIELD, PRODUCT_ATTRIBUTE_ID_FIELD,
    PRODUCT_VARIANT_IDS_FIELD,
    PRODUCT_BULLET_POINT_PREFIX,
    PRODUCT_BULLET_POINT_COUNT,
)


class OdooProductAccess(object):
    """
    This class provides accessing services to Odoo product template
    and variant tables.
    """
    def __init__(self, env):
        self._env = env

    def get_product(self, sync_head):
        model = self._env[sync_head[MODEL_NAME_FIELD]]
        record = model.browse(sync_head[RECORD_ID_FIELD])
        return record

    def get_existed_product(self, sync_head):
        record = self.get_product(sync_head)
        if not record.exists():
            record = None
        return record

    @staticmethod
    def is_product_variant(product):
        return product[PRODUCT_IS_PRODUCT_VARIANT_FIELD]

    @staticmethod
    def is_partial_variant(product):
        result = False
        if OdooProductAccess.is_product_variant(product):
            # a partial variant doesn't have attribute value ids
            if not product[PRODUCT_ATTRIBUTE_VALUE_IDS_FIELD]:
                result = True
        return result

    @staticmethod
    def is_multi_variant_template(product):
        result = False
        if not OdooProductAccess.is_product_variant(product):
            if product[PRODUCT_VARIANT_COUNT_FIELD] > 1:
                result = True
        return result

    def is_partial_variant_multi_template(self, sync_head):
        # is this a partial variant or a multi-variant template?
        result = False
        product = self.get_product(sync_head)
        if OdooProductAccess.is_partial_variant(product):
            result = True
        if OdooProductAccess.is_multi_variant_template(product):
            result = True

        return result

    @staticmethod
    def _get_template_sync_active(product):
        result = False
        for variant in product[PRODUCT_VARIANT_IDS_FIELD]:
            if variant[AMAZON_SYNC_ACTIVE_FIELD]:
                result = True
                break
        return result

    def is_sync_active(self, sync_head):
        product = self.get_product(sync_head)
        if self.is_multi_variant_template(product):
            # a multi-variant template is active if any
            # of its variants is active
            sync_active = self._get_template_sync_active(product)
        else:
            # all other cases, use the field directly
            sync_active = product[AMAZON_SYNC_ACTIVE_FIELD]
        return sync_active

    def get_sku(self, sync_head):
        # for a template that has multi variants,
        # we create a customized SKU
        product = self.get_product(sync_head)
        if self.is_multi_variant_template(product):
            sku = 'Template_' + str(sync_head[RECORD_ID_FIELD])
        else:
            sku = product[PRODUCT_DEFAULT_CODE_FIELD]
        return sku

    @staticmethod
    def get_attributes(product):
        result = []
        rel_attr_table = product[PRODUCT_ATTRIBUTE_VALUE_IDS_FIELD]
        for attr_value in rel_attr_table:
            value = attr_value[PRODUCT_NAME_FIELD]
            name = attr_value[PRODUCT_ATTRIBUTE_ID_FIELD][PRODUCT_NAME_FIELD]
            result.append((name, value))

        return result

    @staticmethod
    def get_bullet_points(product):
        bullet_points = []
        for index in range(1, 1 + PRODUCT_BULLET_POINT_COUNT):
            name = PRODUCT_BULLET_POINT_PREFIX + str(index)
            bullet = product[name]
            if bullet:
                bullet = bullet.strip()
                if bullet:
                    bullet_points.append(bullet)
        return bullet_points
