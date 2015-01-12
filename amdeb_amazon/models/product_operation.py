# -*- coding: utf-8 -*-

from openerp import models, fields

from ..model_names.product_operation import PRODUCT_OPERATION_TABLE


class ProductOperation(models.Model):
    """ add a column to store synchronization status """

    _inherit = [PRODUCT_OPERATION_TABLE]

    # This is set by Sync process regardless the sync results
    amazon_sync_timestamp = fields.Datetime(
        string='Amazon Synchronization Timestamp',
        readonly=True,
    )
