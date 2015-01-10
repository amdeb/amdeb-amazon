# -*- coding: utf-8 -*-

from openerp import models, fields, api

from ..shared.model_names import (
    AMAZON_PRODUCT_SYNC_TABLE,
    PRODUCT_TEMPLATE_TABLE,
    PRODUCT_PRODUCT_TABLE,
)
from ..shared.sync_operation_types import (
    SYNC_CREATE, SYNC_UPDATE, SYNC_DELETE,
    SYNC_PRICE, SYNC_INVENTORY, SYNC_IMAGE,
    SYNC_DEACTIVATE,
)
from ..shared.sync_status import (
    SYNC_STATUS_NEW, SYNC_STATUS_PENDING, SYNC_STATUS_SUCCESS,
    SYNC_STATUS_WARNING, SYNC_STATUS_ERROR, SYNC_STATUS_WAITING,
)
from ..mws import ProductSynchronization


class AmazonProductSync(models.Model):

    _name = AMAZON_PRODUCT_SYNC_TABLE
    _description = 'Amazon Product Synchronization'

    # we use the create date and update date
    _log_access = True

    @api.model
    def synchronize_cron(self):
        env = self.env()
        ProductSynchronization(env).synchronize()

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

    write_field_names = fields.Char(
        string='Write Field Names',
        readonly=True,
    )

    # used in unlink sync
    product_sku = fields.Char(
        string='Product SKU',
        index=True,
        readonly=True,
    )

    sync_status = fields.Selection(
        string='Synchronization Status',
        required=True,
        selection=[
            (SYNC_STATUS_NEW, SYNC_STATUS_NEW),
            (SYNC_STATUS_PENDING, SYNC_STATUS_PENDING),
            (SYNC_STATUS_SUCCESS, SYNC_STATUS_SUCCESS),
            (SYNC_STATUS_WARNING, SYNC_STATUS_WARNING),
            (SYNC_STATUS_ERROR, SYNC_STATUS_ERROR),
            (SYNC_STATUS_WAITING, SYNC_STATUS_WAITING)
        ],
        default=SYNC_STATUS_NEW,
        readonly=True,
    )

    # use both creation timestamp and status count to
    # get clean up old sync operations
    sync_check_status_count = fields.Integer(
        string='The Counter of Submission Status Check',
        required=True,
        default=0,
        readonly=True,
    )

    amazon_request_timestamp = fields.Char(
        string='Amazon Request Timestamp',
        readonly=True,
    )

    # this field stores Amazon processing status and when it is done,
    # the message code for a warning or an error
    amazon_message_code = fields.Char(
        string='Amazon Result Message Code',
        readonly=True,
    )

    amazon_result_description = fields.Text(
        string='Amazon Result Description',
        readonly=True,
    )

    amazon_submission_id = fields.Char(
        string='Amazon Submission Id',
        index=True,
        readonly=True,
    )
