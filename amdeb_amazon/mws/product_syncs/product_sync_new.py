# -*- coding: utf-8 -*-

import logging
from boto.exception import BotoServerError

from ...shared.model_names import (
    SYNC_STATUS_FIELD, AMAZON_MESSAGE_CODE_FIELD,
    AMAZON_REQUEST_TIMESTAMP_FIELD, AMAZON_SUBMISSION_ID_FIELD,
)
from ...shared.sync_operation_types import (
    SYNC_DELETE, SYNC_CREATE, SYNC_DEACTIVATE,
    SYNC_PRICE, SYNC_UPDATE, SYNC_INVENTORY,
    SYNC_IMAGE, SYNC_RELATION,
)
from ...shared.sync_status import SYNC_STATUS_PENDING
from ...models_access import ProductSyncAccess
from ..product_sync_transform import BaseTransformer
from ..product_sync_transform import UpdateTransformer
from ..product_sync_transform import PriceTransformer
from ..product_sync_transform import InventoryTransformer
from ..product_sync_transform import CreateTransformer
from ..product_sync_transform import DeactivateTransformer
from ..product_sync_transform import RelationTransformer

_logger = logging.getLogger(__name__)


class ProductSyncNew(object):
    """
    This class processes new sync operations.
    To match a request with response result, we use
    the sync table record id as the message id
    """
    def _create_sync_types(self):
        delete_sync = (SYNC_DELETE, BaseTransformer, self._mws.send_delete)
        create_sync = (SYNC_CREATE, CreateTransformer, self._mws.send_product)
        # relation syncs are post-creation work, do it early.
        relation_sync = (SYNC_RELATION, RelationTransformer,
                         self._mws.send_relation)
        deactivate_sync = (SYNC_DEACTIVATE, DeactivateTransformer,
                           self._mws.send_inventory)
        update_sync = (SYNC_UPDATE, UpdateTransformer, self._mws.send_product)
        price_sync = (SYNC_PRICE, PriceTransformer, self._mws.send_price)
        inventory_sync = (SYNC_INVENTORY, InventoryTransformer,
                          self._mws.send_inventory)
        image_sync = (SYNC_IMAGE, BaseTransformer, self._mws.send_image)
        # the order matters because delete and create override other syncs
        self._sync_type_tuples = [
            delete_sync, create_sync, relation_sync,
            deactivate_sync, update_sync, price_sync,
            inventory_sync, image_sync,
        ]

    def __init__(self, env, mws):
        self._env = env
        self._mws = mws
        self._product_sync = ProductSyncAccess(env)
        self._create_sync_types()

    @staticmethod
    def _convert_results(results):
        sync_result = {
            SYNC_STATUS_FIELD: SYNC_STATUS_PENDING,
            AMAZON_SUBMISSION_ID_FIELD: results[0],
            AMAZON_REQUEST_TIMESTAMP_FIELD: results[1],
            AMAZON_MESSAGE_CODE_FIELD: results[2],
        }
        return sync_result

    def _mws_send(self, mws_send, syncs, sync_values):
        log_template = "about to call MWS send() for product syncs."
        _logger.debug(log_template.format(len(sync_values)))

        try:
            results = mws_send(sync_values)
            sync_result = self._convert_results(results)
            ProductSyncAccess.update_sync_status(syncs, sync_result)
        except BotoServerError as boto_ex:
            _logger.debug("MWS Request error: {}".format(
                boto_ex.error_code))
            if boto_ex.error_code in ["RequestThrottled",
                                      "ServiceUnavailable"]:
                _logger.debug("Continue with throttled or unavailable error.")
            else:
                ProductSyncAccess.update_sync_new_exception(syncs, boto_ex)
        except Exception as ex:
            # we may want to re-try for recoverable exceptions
            # for now, just report error
            _logger.exception("mws send() threw exception.")
            ProductSyncAccess.update_sync_new_exception(syncs, ex)

    def synchronize(self):
        """
        there are different types of errors: bad request, server
        unavailable, request throttling. It swallows request
        throttling and service unavailable errors for future retry.
        For other error, the call is done with an error.
        """
        _logger.debug("Enter ProductSyncNew synchronize().")

        try:
            # Some waiting syncs may change to new
            # need to check product existence and
            # duplicated/override syncs
            for sync_type_tuple in self._sync_type_tuples:
                sync_type = sync_type_tuple[0]
                sync_ops = self._product_sync.search_new_type(sync_type)
                if sync_ops:
                    log_template = "Got {} new {} syncs."
                    _logger.debug(log_template.format(
                        len(sync_ops), sync_type))

                    transformer = sync_type_tuple[1](self._env)
                    valid_ops, sync_values = transformer.transform(sync_ops)
                    if sync_values:
                        self._mws_send(sync_type_tuple[2],
                                       valid_ops, sync_values)
                    else:
                        _logger.debug("Empty sync values, skipped.")
                else:
                    _logger.debug("No new {} syncs.".format(sync_type))
        except:
            _logger.exception("Exception in ProductSyncNew synchronize().")
