# -*- coding: utf-8 -*-

from ..shared.model_names import(
    MODEL_NAME_FIELD, RECORD_ID_FIELD,
    PRODUCT_PRODUCT_TABLE, PRODUCT_TEMPLATE_TABLE,
    PRODUCT_IS_PRODUCT_VARIANT_FIELD,
    PRODUCT_ATTRIBUTE_VALUE_IDS_FIELD, AMAZON_SYNC_ACTIVE_FIELD,
    PRODUCT_DEFAULT_CODE_FIELD, PRODUCT_VARIANT_COUNT_FIELD,
    PRODUCT_NAME_FIELD, PRODUCT_ATTRIBUTE_ID_FIELD,
    PRODUCT_VARIANT_IDS_FIELD,
)


class OdooProductAccess(object):
    """
    This class provides accessing services to Odoo product template
    and variant tables.
    """
    def __init__(self, env):
        self._env = env

    def is_existed(self, header):
        model_name = header[MODEL_NAME_FIELD]
        record_id = header[RECORD_ID_FIELD]
        table = self._env[model_name]
        return bool(table.browse(record_id).exists())

    @staticmethod
    def is_product_template(header):
        flag = header[MODEL_NAME_FIELD] == PRODUCT_TEMPLATE_TABLE
        return flag

    @staticmethod
    def is_product_variant(self, header):
        flag = header[MODEL_NAME_FIELD] == PRODUCT_PRODUCT_TABLE
        return flag

    def is_partial_variant(self, header):
        """
        Find if a variant is part of its template. If it is
        a variant AND doesn't have attribute value ids, it is a
        partial variant. Otherwise, return False.
        A partial variant is not an independent variant that has attributes.
        :param header: a header that has model name and record id
        :return: True if it's a partial variant, else False
        """
        result = False
        if OdooProductAccess.is_product_variant(header):
            record = self.browse(header)
            if not record[PRODUCT_ATTRIBUTE_VALUE_IDS_FIELD]:
                result = True
        return result

    @staticmethod
    def product_is_variant(product):
        return product[PRODUCT_IS_PRODUCT_VARIANT_FIELD]

    @staticmethod
    def has_multi_variants(product):
        result = False
        if OdooProductAccess.product_is_variant(product):
            if product[PRODUCT_VARIANT_COUNT_FIELD] > 1:
                result = True
        return result

    def browse(self, header):
        model = self._env[header[MODEL_NAME_FIELD]]
        record = model.browse(header[RECORD_ID_FIELD])
        return record

    @staticmethod
    def _get_template_sync_active(product):
        result = False
        for variant in product[PRODUCT_VARIANT_IDS_FIELD]:
            if variant[AMAZON_SYNC_ACTIVE_FIELD]:
                result = True
                break
        return result

    def is_sync_active(self, header):
        product = self.browse(header)
        if self.has_multi_variants(product):
            # a multi-variant template is active if any
            # of its variants is active
            sync_active = self._get_template_sync_active(product)
        else:
            # all other cases, use the field directly
            sync_active = product[AMAZON_SYNC_ACTIVE_FIELD]
        return sync_active

    def get_sku(self, header):
        # for a template that has multi variants,
        # we create a customized SKU
        product = self.browse(header)
        if self.has_multi_variants(product):
            sku = 'Template_' + str(header[RECORD_ID_FIELD])
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
