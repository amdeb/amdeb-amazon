# -*- coding: utf-8 -*-

from ..shared.model_names import (
    AMAZON_PRODUCT_TABLE, MODEL_NAME_FIELD, RECORD_ID_FIELD,
    TEMPLATE_ID_FIELD, PRODUCT_SKU_FIELD, PRODUCT_PRODUCT_TABLE,
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

    def get_by_head(self, sync_head):
        model_name = sync_head[MODEL_NAME_FIELD]
        record_id = sync_head[RECORD_ID_FIELD]
        search_domain = [
            (MODEL_NAME_FIELD, '=', model_name),
            (RECORD_ID_FIELD, '=', record_id)
        ]
        amazon_product = self._table.search(search_domain)
        return amazon_product

    def is_created(self, sync_head):
        header = sync_head
        return bool(self.get_by_head(header))

    def get_variants(self, template_id):
        search_domain = [
            (MODEL_NAME_FIELD, '=', PRODUCT_PRODUCT_TABLE),
            (TEMPLATE_ID_FIELD, '=', template_id)
        ]
        variants = self._table.search(search_domain)
        return variants

    def insert_completed(self, sync_head):
        # insert a new record if it doesn't exist
        if not self.is_created(sync_head):
            product_sku = self._odoo_product.get_sku(sync_head)
            values = {
                MODEL_NAME_FIELD: sync_head[MODEL_NAME_FIELD],
                RECORD_ID_FIELD: sync_head[RECORD_ID_FIELD],
                TEMPLATE_ID_FIELD: sync_head[TEMPLATE_ID_FIELD],
                PRODUCT_SKU_FIELD: product_sku,
            }
            self._table.create(values)
