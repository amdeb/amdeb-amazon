# -*- coding: utf-8 -*-
import logging
from ..shared.model_names import (
    AMAZON_PRODUCT_TABLE, MODEL_NAME_FIELD, RECORD_ID_FIELD,
    TEMPLATE_ID_FIELD, PRODUCT_SKU_FIELD, PRODUCT_PRODUCT_TABLE,
    AMAZON_CREATION_STATUS_FIELD,
)
from ..shared.product_creation_status import (
    PRODUCT_CREATION_WAITING,
    PRODUCT_CREATION_CREATED,
    PRODUCT_CREATION_ERROR,
)
from . import OdooProductAccess
from .sync_head_access import SyncHeadAccess

_logger = logging.getLogger(__name__)


class AmazonProductAccess(SyncHeadAccess):
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

    def get_creation_status(self, sync_head):
        amazon_product = self.get_by_head(sync_head)
        status = amazon_product[AMAZON_CREATION_STATUS_FIELD]
        return status

    def _check_status_by_head(self, sync_head, status_code):
        result = False
        status = self.get_creation_status(sync_head)
        if status == status_code:
            result = True
        return result

    def is_created_by_head(self, sync_head):
        return self._check_status_by_head(sync_head, PRODUCT_CREATION_CREATED)

    def is_waiting_by_head(self, sync_head):
        return self._check_status_by_head(sync_head, PRODUCT_CREATION_WAITING)

    def is_error_by_head(self, sync_head):
        return self._check_status_by_head(sync_head, PRODUCT_CREATION_ERROR)

    @staticmethod
    def _check_status(amazon_product, status_code):
        status = amazon_product[AMAZON_CREATION_STATUS_FIELD]
        return status == status_code

    @staticmethod
    def is_waiting(amazon_product):
        return AmazonProductAccess._check_status(
            amazon_product, PRODUCT_CREATION_WAITING)

    @staticmethod
    def is_created(amazon_product):
        return AmazonProductAccess._check_status(
            amazon_product, PRODUCT_CREATION_CREATED)

    @staticmethod
    def is_error(amazon_product):
        return AmazonProductAccess._check_status(
            amazon_product, PRODUCT_CREATION_ERROR)

    @staticmethod
    def is_waiting_or_created(amazon_product):
        is_waiting = AmazonProductAccess.is_waiting(amazon_product)
        is_created = AmazonProductAccess.is_created(amazon_product)
        return is_waiting or is_created

    def get_variants(self, template_id):
        search_domain = [
            (MODEL_NAME_FIELD, '=', PRODUCT_PRODUCT_TABLE),
            (TEMPLATE_ID_FIELD, '=', template_id)
        ]
        variants = self._table.search(search_domain)
        return variants

    def upsert_creation(self, product_operation):
        amazon_product = self.get_by_head(product_operation)
        if amazon_product:
            if AmazonProductAccess.is_created(amazon_product):
                # once in created status, never change it.
                _logger.debug("Amazon creation status is created, skip.")
            else:
                amazon_product[AMAZON_CREATION_STATUS_FIELD] = (
                    PRODUCT_CREATION_WAITING)
                _logger.debug("Change amazon creation to waiting status.")
        else:
            product_sku = self._odoo_product.get_sku(product_operation)
            values = {
                MODEL_NAME_FIELD: product_operation[MODEL_NAME_FIELD],
                RECORD_ID_FIELD: product_operation[RECORD_ID_FIELD],
                TEMPLATE_ID_FIELD: product_operation[TEMPLATE_ID_FIELD],
                PRODUCT_SKU_FIELD: product_sku,
            }
            self._table.create(values)
            _logger.debug("Insert a new amazon product record. ")

    def _update_creation_status(self, sync_head, creation_status):
        # insert a new record if it doesn't exist
        amazon_product = self.get_by_head(sync_head)
        if amazon_product:
            # once in created status, never change it.
            if AmazonProductAccess.is_created(amazon_product):
                _logger.debug("Amazon creation status is created, skip.")
            else:
                amazon_product[AMAZON_CREATION_STATUS_FIELD] = creation_status
                log_template = "Change amazon creation status to {0}. "
                _logger.debug(log_template.format(creation_status))
        else:
            _logger.debug("Unable to find product creation record, skip.")

    def update_created(self, sync_head):
        self._update_creation_status(sync_head, PRODUCT_CREATION_CREATED)

    def update_error(self, sync_head):
        self._update_creation_status(sync_head, PRODUCT_CREATION_ERROR)

    @staticmethod
    def unlink_record(record):
        record.unlink()
