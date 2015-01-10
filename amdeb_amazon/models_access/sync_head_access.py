# -*- coding: utf-8 -*-

from ..shared.model_names import(
    MODEL_NAME_FIELD,
    PRODUCT_TEMPLATE_TABLE,
    PRODUCT_PRODUCT_TABLE,
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
