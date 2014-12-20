# -*- coding: utf-8 -*-

from ..shared.model_names import(
    PRODUCT_TEMPLATE_TABLE,
    PRODUCT_VARIANT_COUNT_FIELD,
    MODEL_NAME_FIELD,
    RECORD_ID_FIELD,
    AMAZON_SYNC_ACTIVE_FIELD,
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

    def has_multi_variants(self, template_id):
        result = False
        template = self._env[PRODUCT_TEMPLATE_TABLE]
        record = template.browse(template_id)
        if record[PRODUCT_VARIANT_COUNT_FIELD] > 1:
            result = True
        return result

    def get_sync_active(self, header):
        model = self._env[header[MODEL_NAME_FIELD]]
        record = model.browse(header[RECORD_ID_FIELD])
        sync_active = record[AMAZON_SYNC_ACTIVE_FIELD]
        return sync_active
