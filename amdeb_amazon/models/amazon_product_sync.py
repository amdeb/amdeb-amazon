# -*- coding: utf-8 -*-

import logging

from openerp import models, fields, api

from ..shared.model_names import (
    AMAZON_INTEGRATOR_TABLE,
    PRODUCT_TEMPLATE,
    PRODUCT_PRODUCT,
    SYNC_CREATE,
    SYNC_UPDATE,
    SYNC_DELETE,
    SYNC_PRICE,
    SYNC_INVENTORY,
    SYNC_IMAGE,
    SYNC_DEACTIVATE,
)
from ..shared.integration_status import (
    PENDING_STATUS,
    SUCCESS_STATUS,
    ERROR_STATUS,
)
from ..shared.utility import field_utcnow
from ..mws import Synchronization

_logger = logging.getLogger(__name__)


class AmazonProductSync(models.Model):

    _name = AMAZON_INTEGRATOR_TABLE
    _description = 'Amazon Product Synchronization'
    _log_access = False

    @api.model
    def synchronize_cron(self):
        _logger.info("Amazon Synchronization cron job running")
        Synchronization(self.env).synchronize()

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
        required=True,
        default=False,
        readonly=True,
    )

    sync_status = fields.Selection(
        string='Synchronization Status',
        required=True,
        selection=[(PENDING_STATUS, PENDING_STATUS),
                   (SUCCESS_STATUS, SUCCESS_STATUS),
                   (ERROR_STATUS, ERROR_STATUS),
                   ],
        default=PENDING_STATUS,
        readonly=True,
    )

    sync_message = fields.Text(
        string='Synchronization Response Result',
        readonly=True,
    )

    sync_start_time = fields.Datetime(
        string='Synchronization Start Timestamp',
        required=True,
        default=field_utcnow,
        index=True,
        readonly=True,
    )

    sync_end_time = fields.Datetime(
        string='Synchronization End Timestamp',
        index=True,
        readonly=True,
    )
