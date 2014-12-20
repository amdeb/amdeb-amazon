# -*- coding: utf-8 -*-

from ..shared.model_names import(
    PRODUCT_PRODUCT_TABLE, MODEL_NAME_FIELD, RECORD_ID_FIELD,
    ATTRIBUTE_VALUE_IDS_FIELD, AMAZON_SYNC_ACTIVE_FIELD,
    PRODUCT_DEFAULT_CODE_FIELD,
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

    def is_partial_variant(self, record_id):
        """
        Find if a variant is part of its template.
        In other words, it is not an independent variant that has attributes.
        :param record_id: the id of a product variant
        :return: True if it's a partial variant, else False
        """
        result = False
        template = self._env[PRODUCT_PRODUCT_TABLE]
        record = template.browse(record_id)
        if record[ATTRIBUTE_VALUE_IDS_FIELD]:
            result = True
        return result

    def browse(self, header):
        model = self._env[header[MODEL_NAME_FIELD]]
        record = model.browse(header[RECORD_ID_FIELD])
        return record

    def is_sync_active(self, header):
        record = self.browse(header)
        sync_active = record[AMAZON_SYNC_ACTIVE_FIELD]
        return sync_active

    def get_sku(self, header):
        record = self.browse(header)
        sku = record[PRODUCT_DEFAULT_CODE_FIELD]
        return sku
