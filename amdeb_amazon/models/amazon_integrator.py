# -*- coding: utf-8 -*-

import logging

from openerp import models, fields, api

from ..shared.model_names import AMAZON_INTEGRATOR_TABLE
from ..shared.integration_status import (
    NEW_STATUS,
    SUCCESS_STATUS,
    ERROR_STATUS,
)
from ..shared.utility import field_utcnow
from ..mws import Synchronization

_logger = logging.getLogger(__name__)


class AmazonIntegrator(models.Model):
    """ add a column to store synchronization status """

    _name = AMAZON_INTEGRATOR_TABLE
    _description = 'Amazon Integration Job Log'
    _log_access = False

    @api.model
    def synchronize_cron(self):
        _logger.info("Amazon Synchronization cron job running")

        # write the start time
        record = self.create({})
        values = {}
        try:
            result = Synchronization(self.env).synchronize()
            values['sync_status'] = SUCCESS_STATUS
        except Exception as e:
            result = e.message
            values['sync_status'] = ERROR_STATUS
            _logger.exception("Exception threw in Amazon Synchronization.")

        values['sync_response'] = result
        values['sync_end_time'] = field_utcnow()
        record.write(values)

    sync_status = fields.Selection(
        string='Synchronization Status',
        required=True,
        selection=[(NEW_STATUS, NEW_STATUS),
                   (SUCCESS_STATUS, SUCCESS_STATUS),
                   (ERROR_STATUS, ERROR_STATUS),
                   ],
        default=NEW_STATUS,
        readonly=True,
    )

    sync_response = fields.Text(
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
