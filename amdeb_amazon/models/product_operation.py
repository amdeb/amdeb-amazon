# -*- coding: utf-8 -*-

from openerp import models, fields

from ..shared.model_names import PRODUCT_OPERATION_TABLE
from ..shared.integration_status import (
    NEW_STATUS,
    SYNCHRONIZING_STATUS,
    SYNCHRONIZED_STATUS,
    ERROR_STATUS,
)


class ProductOperation(models.Model):
    """ add a column to store synchronization status """

    _inherit = [PRODUCT_OPERATION_TABLE]

    amazon_sync_status = fields.Selection(
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
