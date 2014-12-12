# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from openerp import models, fields, api

from ..shared.model_names import (
    AMAZON_PRODUCT_SYNC_TABLE,
    PRODUCT_TEMPLATE,
    PRODUCT_PRODUCT,
)
from ..shared.sync_operation_types import (
    SYNC_CREATE,
    SYNC_UPDATE,
    SYNC_DELETE,
    SYNC_PRICE,
    SYNC_INVENTORY,
    SYNC_IMAGE,
    SYNC_DEACTIVATE,
)
from ..shared.sync_status import (
    SYNC_NEW,
    SYNC_PENDING,
    SYNC_SUCCESS,
    SYNC_ERROR,
)
from ..shared.utility import field_utcnow
from ..mws import ProductSynchronization


class AmazonProductSync(models.Model):

    _name = AMAZON_PRODUCT_SYNC_TABLE
    _description = 'Amazon Product Synchronization'
    _log_access = False

    @api.model
    def synchronize_cron(self):
        _logger.info("Amazon Synchronization cron job running")
        env = self.env()
        ProductSynchronization(env).synchronize()

    model_name = fields.Selection(
        string='Model Name',
        required=True,
        selection=[(PRODUCT_PRODUCT, PRODUCT_PRODUCT),
                   (PRODUCT_TEMPLATE, PRODUCT_TEMPLATE),
                   ],
        readonly=True,
    )

    record_id = fields.Integer(
        string='Record Id',
        required=True,
        index=True,
        readonly=True,
    )

    template_id = fields.Integer(
        string='Product Template Id',
        required=True,
        index=True,
        readonly=True,
    )

    sync_type = fields.Selection(
        string='Synchronization Type',
        required=True,
        selection=[
            (SYNC_CREATE, SYNC_CREATE),
            (SYNC_UPDATE, SYNC_UPDATE),
            (SYNC_DELETE, SYNC_DELETE),
            (SYNC_PRICE, SYNC_PRICE),
            (SYNC_INVENTORY, SYNC_INVENTORY),
            (SYNC_IMAGE, SYNC_IMAGE),
            (SYNC_DEACTIVATE, SYNC_DEACTIVATE),
        ],
        readonly=True,
    )

    sync_data = fields.Binary(
        string='Synchronization Data',
        readonly=True,
    )

    sync_status = fields.Selection(
        string='Synchronization Status',
        required=True,
        selection=[
            (SYNC_NEW, SYNC_NEW),
            (SYNC_PENDING, SYNC_PENDING),
            (SYNC_SUCCESS, SYNC_SUCCESS),
            (SYNC_ERROR, SYNC_ERROR),
        ],
        default=SYNC_NEW,
        readonly=True,
    )

    sync_creation_timestamp = fields.Datetime(
        string='Synchronization Creation Timestamp',
        required=True,
        default=field_utcnow,
        readonly=True,
    )

    sync_response_timestamp = fields.Datetime(
        string='Synchronization Response Timestamp',
        readonly=True,
    )

    sync_response_message = fields.Text(
        string='Synchronization Response Message',
        readonly=True,
    )

    sync_response_status = fields.Char(
        string='Synchronization Response Status Code',
        readonly=True,
    )

    sync_response_request_id = fields.Char(
        string='Synchronization Response Request Id',
        readonly=True,
    )
