# -*- coding: utf-8 -*-

from ..shared.model_names import (
    AMAZON_PRODUCT_TABLE, MODEL_NAME_FIELD, RECORD_ID_FIELD,
    TEMPLATE_ID_FIELD, PRODUCT_SKU_FIELD,

    PRODUCT_PRODUCT_TABLE, PRODUCT_DEFAULT_CODE_FIELD,
)

from . import OdooProductAccess

class AmazonProductAccess(object):
    """
    This class provides methods accessing Amazon Product Table
    that stores created product head and SKU.
    """
    def __init__(self, env):
        self._table = env[AMAZON_PRODUCT_TABLE]
        self._odoo_product = OdooProductAccess(env)

    def search(self, sync_head):
        model_name = sync_head[MODEL_NAME_FIELD]
        record_id = sync_head[RECORD_ID_FIELD]
        search_domain = [
            (MODEL_NAME_FIELD, '=', model_name),
            (RECORD_ID_FIELD, '=', record_id)
        ]
        amazon_product = self._table.search(search_domain)
        return amazon_product

    def is_created(self, sync_head):
        return bool(self.search(sync_head))

    def get_variants(self, template_id):
        search_domain = [
            (MODEL_NAME_FIELD, '=', PRODUCT_PRODUCT_TABLE),
            (TEMPLATE_ID_FIELD, '=', template_id)
        ]
        variants = self._table.search(search_domain)
        return variants

    def get_created_variants(self, template_id):
        headers = []
        search_domain = [
            (MODEL_NAME_FIELD, '=', PRODUCT_PRODUCT_TABLE),
            (TEMPLATE_ID_FIELD, '=', template_id)
        ]

        variants = self._table.search(search_domain)
        for variant in variants:
            record_id = variant[RECORD_ID_FIELD]
            header = {
                MODEL_NAME_FIELD: PRODUCT_PRODUCT_TABLE,
                RECORD_ID_FIELD: record_id,
                TEMPLATE_ID_FIELD: template_id,
            }
            headers.append(header)
        return headers

    def write_from_sync(self, sync_head):
        product = self._odoo_product.browse(sync_head)
        product_sku = product[PRODUCT_DEFAULT_CODE_FIELD]
        values = {
            MODEL_NAME_FIELD: sync_head[MODEL_NAME_FIELD],
            RECORD_ID_FIELD: sync_head[RECORD_ID_FIELD],
            TEMPLATE_ID_FIELD: sync_head[TEMPLATE_ID_FIELD],
            PRODUCT_SKU_FIELD: product_sku,
        }
        self._table.create(values)
