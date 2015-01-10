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

    def browse(self, sync_head):
        model = self._env[sync_head[MODEL_NAME_FIELD]]
        record = model.browse(sync_head[RECORD_ID_FIELD])
        return record

    def is_existed(self, sync_head):
        record = self.browse(sync_head)
        return bool(record.exists())

    @staticmethod
    def product_is_variant(product):
        return product[PRODUCT_IS_PRODUCT_VARIANT_FIELD]

    def is_partial_variant(self, sync_head):
        """
        Find if a variant is part of its template. If it is
        a variant AND doesn't have attribute value ids, it is a
        partial variant. Otherwise, return False.
        A partial variant is not an independent variant that has attributes.
        :param sync_head: a head that has model name and record id
        :return: True if it's a partial variant, else False
        """
        result = False
        record = self.browse(sync_head)
        if record and OdooProductAccess.product_is_variant(record):
            if not record[PRODUCT_ATTRIBUTE_VALUE_IDS_FIELD]:
                result = True
        return result

    @staticmethod
    def has_multi_variants(product):
        result = False
        if OdooProductAccess.product_is_variant(product):
            if product[PRODUCT_VARIANT_COUNT_FIELD] > 1:
                result = True
        return result

    def is_multi_variant(self, sync_head):
        result = False
        record = self.browse(sync_head)
        if record:
            result = OdooProductAccess.has_multi_variants(record)
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
        product = self.browse(sync_head)
        if self.has_multi_variants(product):
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
        product = self.browse(sync_head)
        if self.has_multi_variants(product):
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
