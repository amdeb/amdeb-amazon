# -*- coding: utf-8 -*-

from openerp import models, fields

from ..shared.model_names import PRODUCT_PRODUCT_TABLE


class product_product(models.Model):
    _inherit = [PRODUCT_PRODUCT_TABLE]

    # we don't care about the product 'active' field
    # set default to False to let use fill all data and
    # start sync
    amazon_sync_active = fields.Boolean(
        string="Amazon Sync Active Flag",
        default=False,
    )
