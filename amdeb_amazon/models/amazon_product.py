# -*- coding: utf-8 -*-

from openerp import models, fields

from ..model_names.product_template import PRODUCT_TEMPLATE_TABLE
from ..model_names.product_product import PRODUCT_PRODUCT_TABLE
from ..model_names.amazon_product import (
    AMAZON_PRODUCT_TABLE, PRODUCT_CREATION_WAITING,
    PRODUCT_CREATION_CREATED, PRODUCT_CREATION_ERROR,
)


class AmazonProductSync(models.Model):
    """
    A product (a template or non-partial variant) here may be in
    one of three status: waiting creation, amazon created, creation error.
    We create a record in waiting creation before we send a create request.
    A newly created recode has the creation waiting status.
    If the status changes to created, all pending requests
    will be processed. If the status changes to error, all pending requests
    will be marked as Error if there is no pending create request.

    If it is in waiting status, all syncs for this records will be in
    waiting status.
    If it is in created status, all syncs will be processed.
    If it is in error status, all syncs will be marked as error.
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

    # Amazon mixes creation and updating.
    # Once created, we never change it back to Waiting/Error.
    # Before success, the status switches between Waiting and Error
    creation_status = fields.Selection(
        string='Amazon Creation Status',
        required=True,
        selection=[(PRODUCT_CREATION_WAITING, PRODUCT_CREATION_WAITING),
                   (PRODUCT_CREATION_CREATED, PRODUCT_CREATION_CREATED),
                   (PRODUCT_CREATION_ERROR, PRODUCT_CREATION_ERROR),
                   ],
        default=PRODUCT_CREATION_WAITING,
        readonly=True,
    )
