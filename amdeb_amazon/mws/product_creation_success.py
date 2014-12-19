# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from ..shared.model_names import (
    PRODUCT_PRODUCT_TABLE,
    MODEL_NAME_FIELD,
    RECORD_ID_FIELD,
    SYNC_STATUS_FIELD,
    SYNC_TYPE_FIELD,
    AMAZON_SYNC_ACTIVE_FIELD,
    PRODUCT_PRICE_FIELD,
    PRODUCT_AVAILABLE_QUANTITY_FIELD,
    PRODUCT_VARIANT_COUNT_FIELD,
)
from ..shared.sync_status import SYNC_ERROR
from ..shared.sync_operation_types import SYNC_CREATE

from .product_sync_access import ProductSyncAccess
from .amazon_product_access import AmazonProductAccess
from .product_utility import ProductUtility


class ProductCreationSuccess(object):
    def __init__(self, env):
        self._env = env
        self._sync_creation = ProductSyncAccess(env)
        self._amazon_product_access = AmazonProductAccess(env)
        self._product_utility = ProductUtility(env)
        self._is_new_sync_added = False

    def _add_price_sync(self, record, completed):
        price = record[PRODUCT_PRICE_FIELD]
        self._sync_creation.insert_price(completed, price)

    def _add_inventory_sync(self, record, completed):
        inventory = record[PRODUCT_AVAILABLE_QUANTITY_FIELD]
        self._sync_creation.insert_inventory(completed, inventory)

    def _add_success_syncs(self, record, completed):
        self._add_price_sync(record, completed)
        self._add_inventory_sync(record, completed)
        self._sync_creation.insert_image(completed)

    def _write_creation_success(self, completed):
        model_name = completed[MODEL_NAME_FIELD]
        record_id = completed[RECORD_ID_FIELD]
        _logger.debug("write creation success for {0}, {1}".format(
            model_name, record_id
        ))
        record = self._env[model_name].browse(record_id)
        sync_active = record[AMAZON_SYNC_ACTIVE_FIELD]
        if sync_active:
            self._add_success_syncs(record, completed)
            self._is_new_sync_added = True

    def _check_variant_created(self, completed):
        headers = []
        model_name = completed[MODEL_NAME_FIELD]
        template_id = completed[RECORD_ID_FIELD]
        template_record = self._env[model_name].browse(template_id)
        if template_record[PRODUCT_VARIANT_COUNT_FIELD] > 1:
            headers = self._amazon_product_access.get_created_variants(
                template_id)
        return headers

    def _add_relation_sync(self, completed):
        # It is possible that a product template or variant
        # creation is failed and the relation
        # is not created for a product variant.
        # The automatic way to fix this is to create
        # relation syn for both template and variant creation sync
        if completed[MODEL_NAME_FIELD] == PRODUCT_PRODUCT_TABLE:
            if self._amazon_product_access.is_created(completed):
                self._sync_creation.insert_relation(completed)
            else:
                log_template = "Product template is not created for {}. " \
                               "Don't create relation sync"
                _logger.debug(log_template.format(
                    completed[RECORD_ID_FIELD]
                ))
        else:
            headers = self._check_variant_created(completed)
            for header in headers:
                self._sync_creation.insert_relation(header)

    def process(self, completed_set):
        for completed in completed_set:
            # for warning and success, set success flag
            is_success = completed[SYNC_STATUS_FIELD] != SYNC_ERROR
            is_sync_create = completed[SYNC_TYPE_FIELD] == SYNC_CREATE
            if is_sync_create and is_success:
                # make sure that the product is still there
                if self._product_utility.is_existed(completed):
                    self._write_creation_success(completed)
                    self._amazon_product_access.write_from_sync(completed)
                    self._add_relation_sync(completed)
                else:
                    log_template = "Skip creation success for unlinked " \
                                   "Model: {0}, Record Id: {1}."
                    _logger.debug(log_template.format(
                        completed[MODEL_NAME_FIELD],
                        completed[RECORD_ID_FIELD]
                    ))
        return self._is_new_sync_added
