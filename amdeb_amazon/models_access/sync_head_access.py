# -*- coding: utf-8 -*-

from ..shared.model_names import(
    MODEL_NAME_FIELD,
    PRODUCT_TEMPLATE_TABLE,
    PRODUCT_PRODUCT_TABLE,
    WRITE_FIELD_NAMES_FIELD,
    FIELD_NAME_DELIMITER
)

class SyncHeadAccess(object):
    """
    The base class used to define common methods for
    sync head fields thus each sync_head can use its own access class.
    """
    @staticmethod
    def is_product_template(sync_head):
        return sync_head[MODEL_NAME_FIELD] == PRODUCT_TEMPLATE_TABLE

    @staticmethod
    def is_product_variant(sync_head):
        return sync_head[MODEL_NAME_FIELD] == PRODUCT_PRODUCT_TABLE

    @staticmethod
    def get_write_field_names(sync_head):
        field_names = sync_head[WRITE_FIELD_NAMES_FIELD]
        if field_names:
            data = set(field_names.split(FIELD_NAME_DELIMITER))
        else:
            data = set()
        return data

    @staticmethod
    def save_write_field_names(sync_head, write_fields):
        joined = FIELD_NAME_DELIMITER.join(write_fields)
        sync_head[WRITE_FIELD_NAMES_FIELD] = joined
