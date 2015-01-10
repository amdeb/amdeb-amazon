# -*- coding: utf-8 -*-

from openerp import models, fields

from ..shared.model_names import (
    AMAZON_PRODUCT_TABLE,
    PRODUCT_TEMPLATE_TABLE,
    PRODUCT_PRODUCT_TABLE,
)
from ..shared.product_creation_status import (
    PRODUCT_CREATION_WAITING,
    PRODUCT_CREATION_CREATED,
    PRODUCT_CREATION_ERROR,
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
