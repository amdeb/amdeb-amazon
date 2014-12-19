# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from ..shared.model_names import (
    PRODUCT_TEMPLATE_TABLE,
    MODEL_NAME_FIELD,
    RECORD_ID_FIELD,
    TEMPLATE_ID_FIELD,
    OPERATION_TYPE_FIELD,
)

from ..shared.db_operation_types import UNLINK_RECORD

from .product_sync_creation import ProductSyncCreation
from .amazon_product_access import AmazonProductAccess


class ProductUnlinkTransformer(object):

    def __init__(self, env, new_operations):
        self._env = env
        self._new_operations = new_operations
        self._sync_creation = ProductSyncCreation(env)
        self._amazon_product_access = AmazonProductAccess(env)

    def _check_template_unlink(self, operation):
        found = False
        template_unlink = [
            element for
            element in self._new_operations if
            element[MODEL_NAME_FIELD] == PRODUCT_TEMPLATE_TABLE and
            element[RECORD_ID_FIELD] == operation[TEMPLATE_ID_FIELD] and
            element[OPERATION_TYPE_FIELD] == UNLINK_RECORD
        ]
        if template_unlink:
            found = True
        return found

    def _add_template_unlink(self, amazon_product_template):
        template_id = amazon_product_template[RECORD_ID_FIELD]
        amazon_variants = self._amazon_product_access.get_variants(
            template_id
        )
        for variant in amazon_variants:
            self._sync_creation.insert_amazon_delete(variant)
            variant.unlink()
        self._sync_creation.insert_amazon_delete(amazon_product_template)
        amazon_product_template.unlink()

    def transform(self, operation):
        """
        Unlink a product if it is created in Amazon, even
        its sync active flag is False because
        keeping it in Amazon will cause many confusing when
        we download reports, history etc but couldn't find
        it locally.

        For template unlink, unlink all its variants.
        Ignore a variant unlink if its template unlink appears

        We also delete unlinked records in amazon_product table
        """
        amazon_product = self._amazon_product_access.get_amazon_product(
            operation)
        if amazon_product:
            if operation[MODEL_NAME_FIELD] == PRODUCT_TEMPLATE_TABLE:
                self._add_template_unlink(amazon_product)
            else:
                if self._check_template_unlink(operation):
                    log_template = "Use template unlink operation " \
                                   "for variant Model: {0}, Record id: {1}"
                    _logger.debug(log_template.format(
                        operation[MODEL_NAME_FIELD],
                        operation[RECORD_ID_FIELD]
                    ))
                else:
                    self._sync_creation.insert_amazon_delete(amazon_product)
                    amazon_product.unlink()
        else:
            log_template = "Product is not created in Amazon for unlink " \
                           "operation for Model: {0}, Record id: {1}"
            _logger.debug(log_template.format(
                operation[MODEL_NAME_FIELD], operation[RECORD_ID_FIELD]
            ))
