# -*- coding: utf-8 -*-

import logging

from ...shared.model_names import (
    RECORD_ID_FIELD, TEMPLATE_ID_FIELD,
    OPERATION_TYPE_FIELD,
)
from .operation_types import UNLINK_RECORD

from ...models_access import ProductSyncAccess
from ...models_access import AmazonProductAccess
from ...models_access import ProductOperationAccess

_logger = logging.getLogger(__name__)


class ProductUnlinkTransformer(object):
    """
    Create unlink sync records and delete
    Amazon product records for unlinked products
    """
    def __init__(self, env, new_operations):
        # we need new operations to find template unlink operation
        self._new_operations = new_operations
        self._product_sync = ProductSyncAccess(env)
        self._amazon_product = AmazonProductAccess(env)

    def _check_template_unlink(self, operation):
        found = False
        templates = [
            element for element in self._new_operations if
            ProductOperationAccess.is_product_template(element) and
            element[RECORD_ID_FIELD] == operation[TEMPLATE_ID_FIELD] and
            element[OPERATION_TYPE_FIELD] == UNLINK_RECORD
        ]
        if templates:
            found = True
        return found

    # use this method to consistently add a sync record
    # AND delete from amazon product table in one call
    def _sync_and_delete(self, amazon_product):
        self._product_sync.insert_delete(amazon_product)
        self._amazon_product.unlink_record(amazon_product)

    def _add_template_unlink(self, template):
        template_id = template[RECORD_ID_FIELD]
        amazon_variants = self._amazon_product.get_variants(template_id)
        for variant in amazon_variants:
            self._sync_and_delete(variant)
        self._sync_and_delete(template)

    def transform(self, operation):
        """
        Delete a product if it is created or creation waiting in Amazon,
        even its sync active flag is False because keeping it
        in Amazon will cause many confuses when
        we download reports, history etc but couldn't find
        it locally.

        For template unlink, unlink all its variants.
        Ignore a variant unlink if its template unlink appears

        We also delete unlinked records in amazon_product table
        after the unlink syncs are created
        """
        amazon_product = self._amazon_product.search_by_head(operation)
        if AmazonProductAccess.is_waiting_or_created(amazon_product):
            # for a waiting or created product, just send delete request
            if ProductOperationAccess.is_product_template(operation):
                self._add_template_unlink(amazon_product)
            else:
                if self._check_template_unlink(operation):
                    _logger.debug("Found template unlink operation. "
                                  "Skip variant unlink.")
                else:
                    self._sync_and_delete(amazon_product)
        else:
            # this include partial variant unlink
            _logger.debug("Product is not created in Amazon or has no "
                          "waiting creation. Skip unlink.")
