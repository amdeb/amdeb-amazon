# -*- coding: utf-8 -*-

from openerp import models, fields

from ..shared.model_names import (
    AMAZON_PRODUCT_TABLE,

    PRODUCT_TEMPLATE_TABLE,
    PRODUCT_PRODUCT_TABLE,
)


class AmazonProductSync(models.Model):
    """
    This table stores SKUs for products that are
    successfully created in Amazon.
    A record is deleted when the product is unlinked
    """
    _name = AMAZON_PRODUCT_TABLE
    _description = 'Created Amazon Product'
    _log_access = False

    model_name = fields.Selection(
        string='Model Name',
        required=True,
        selection=[
            (PRODUCT_PRODUCT_TABLE, PRODUCT_PRODUCT_TABLE),
            (PRODUCT_TEMPLATE_TABLE, PRODUCT_TEMPLATE_TABLE),
        ],
        readonly=True,
    )

    record_id = fields.Integer(
        string='Record Id',
        required=True,
        index=True,
        readonly=True,
    )

    # this helps to unlink all variant when a
    # template is unlinked
    template_id = fields.Integer(
        string='Product Template Id',
        required=True,
        index=True,
        readonly=True,
    )

    product_sku = fields.Char(
        string='Product SKU',
        required=True,
        index=True,
        readonly=True,
    )
