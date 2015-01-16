# -*- coding: utf-8 -*-

import logging

from .base_transfomer import BaseTransformer
from ...model_names.shared_names import (
    RECORD_ID_FIELD, PRODUCT_SKU_FIELD,
)
from ..amazon_names import (
    AMAZON_PARENT_SKU_FIELD,
    AMAZON_VARIANTS_FIELD,
)

_logger = logging.getLogger(__name__)


class RelationTransformer(BaseTransformer):
    """
    Create relation for a product template sync record
    """
    def _convert_sync(self, sync_op):
        sync_value = super(RelationTransformer, self)._convert_sync(sync_op)
        amazon_product = self._amazon_product.search_by_head(sync_op)
        sync_value[AMAZON_PARENT_SKU_FIELD] = amazon_product[PRODUCT_SKU_FIELD]

        sync_value[AMAZON_VARIANTS_FIELD] = []
        template_id = sync_op[RECORD_ID_FIELD]
        created_variants = self._amazon_product.get_variants(template_id)
        has_variant = False
        for variant in created_variants:
            has_variant = True
            sync_value[AMAZON_VARIANTS_FIELD].append(
                variant[PRODUCT_SKU_FIELD])

        if not has_variant:
            sync_value = None
        return sync_value
