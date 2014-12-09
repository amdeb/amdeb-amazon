# -*- coding: utf-8 -*-

from openerp import models, fields

from ..shared.model_names import PRODUCT_OPERATION_TABLE


class ProductOperation(models.Model):
    """ add a column to store synchronization status """

    _inherit = [PRODUCT_OPERATION_TABLE]

    amazon_sync_timestamp = fields.Datetime(
        string='Amazon Synchronization Timestamp',
        readonly=True,
    )
