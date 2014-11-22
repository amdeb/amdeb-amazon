# -*- coding: utf-8 -*-

import logging

from openerp import models, fields

from ..shared.model_names import (
    AMAZON_INTEGRATOR_TABLE,
    PRODUCT_OPERATION_TABLE,
    PRODUCT_TEMPLATE,
    PRODUCT_PRODUCT,
    IR_VALUES,
    AMAZON_SETTINGS_TABLE,
)
from ..shared.integration_status import (
    NEW_STATUS,
    SYNCHRONIZING_STATUS,
    SYNCHRONIZED_STATUS,
    ERROR_STATUS,
)
from ..shared.utility import field_utcnow

_logger = logging.getLogger(__name__)


class AmazonIntegrator(models.Model):
    """ add a column to store synchronization status """

    _name = AMAZON_INTEGRATOR_TABLE
    _description = 'Amazon Integration Job Log'
    _log_access = False

    def _get_settings(self):
        ir_values = self.env[IR_VALUES]
        self.settings = ir_values.get_defaults_dict(AMAZON_SETTINGS_TABLE)

    def synchronize_cron(self, cr, uid, context=None):
        _logger.info("Amazon Synchronization running")
        self.create()
        self._get_settings()

        result = {
            'sync_status': SYNCHRONIZED_STATUS,
            'sync_response': str(self.settings),
            'sync_end_time': field_utcnow(),
        }
        self.write(result)

    sync_status = fields.Selection(
        string='Synchronization Status',
        required=True,
        selection=[(NEW_STATUS, NEW_STATUS),
                   (SYNCHRONIZING_STATUS, SYNCHRONIZING_STATUS),
                   (SYNCHRONIZED_STATUS, SYNCHRONIZED_STATUS),
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
        required=True,
        index=True,
        readonly=True,
    )


