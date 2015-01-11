# -*- coding: utf-8 -*-

import logging

from .base_transfomer import BaseTransformer
from ...shared.model_names import RECORD_ID_FIELD, PRODUCT_SKU_FIELD

_logger = logging.getLogger(__name__)


class RelationTransformer(BaseTransformer):
    """
    Create relation for a product template sync record
    """
    def _convert_sync(self, sync_op):
        sync_value = super(RelationTransformer, self)._convert_sync(sync_op)
        template_id = sync_op[RECORD_ID_FIELD]
        sync_value['ParentSKU'] = sync_op[PRODUCT_SKU_FIELD]
        sync_value['Variants'] = []
        created_variants = self._amazon_product.get_variants(template_id)
        has_variant = False
        for variant in created_variants:
            has_variant = True
            sync_value['Variants'].append(variant[PRODUCT_SKU_FIELD])

        if not has_variant:
            sync_value = None
        return sync_value
