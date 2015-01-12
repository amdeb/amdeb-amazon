# -*- coding: utf-8 -*-

from openerp import models, fields, api

from ..model_names.product_template import PRODUCT_TEMPLATE_TABLE
from ..model_names.product_product import PRODUCT_PRODUCT_TABLE
from ..model_names.product_sync import (
    AMAZON_PRODUCT_SYNC_TABLE,
    SYNC_CREATE, SYNC_UPDATE, SYNC_DELETE,
    SYNC_PRICE, SYNC_INVENTORY, SYNC_IMAGE,
    SYNC_DEACTIVATE, SYNC_RELATION,
    SYNC_STATUS_NEW, SYNC_STATUS_PENDING,
    SYNC_STATUS_SUCCESS, SYNC_STATUS_WARNING,
    SYNC_STATUS_ERROR, SYNC_STATUS_WAITING,
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
        index=True,
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
            (SYNC_RELATION, SYNC_RELATION)
        ],
        index=True,
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

    # When created, a sync is in New or Waiting status
    # Default is New. It is Waiting when the Amazon Product
    # is waiting for creation. When a product is created
    # successfully, the Waiting status of its syncs switches to
    # New. When a product creation failed, the Waiting status of
    # its sync switches to Error.
    #
    # Each synchronization run sends New Syncs to Amazon. When there is a
    # submission id, a New sync becomes a Pending sync. If there
    # is no submission id or mws call fails, its status becomes Error.
    # Because mws call library has built-in retry, we don't re-try
    # it in anther synchronization run except for exceptions
    # such as Server unavailable or request throttling.
    # These exceptions are temporal conditions that stop the
    # synchronization process without changing the New sync status.
    #
    # Every synchronization run checks Pending syncs and increase
    # its counter. If a New sync meets archive condition,
    # its status becomes Error in daily chore. If its submission
    # is complete, its status could be Success, Warning, or Error.
    #
    # The life of a sync starts in New or Waiting and ends in one of
    # Success, Warning, or Error status
    sync_status = fields.Selection(
        string='Synchronization Status',
        required=True,
        selection=[
            # stage 1, beginning of life
            (SYNC_STATUS_NEW, SYNC_STATUS_NEW),
            (SYNC_STATUS_WAITING, SYNC_STATUS_WAITING),

            # stage 2, has a submission id
            (SYNC_STATUS_PENDING, SYNC_STATUS_PENDING),

            # stage 3, the final status of life
            (SYNC_STATUS_SUCCESS, SYNC_STATUS_SUCCESS),
            (SYNC_STATUS_WARNING, SYNC_STATUS_WARNING),
            (SYNC_STATUS_ERROR, SYNC_STATUS_ERROR),
        ],
        default=SYNC_STATUS_NEW,
        index=True,
        readonly=True,
    )

    # use with creation timestamp to archive old syncs.
    # it increases by one before checking status for pending syncs
    sync_check_status_count = fields.Integer(
        string='The Counter of Submission Status Check',
        required=True,
        default=0,
        readonly=True,
    )

    amazon_request_timestamp = fields.Char(
        string='Amazon Request Timestamp',
        index=True,
        readonly=True,
    )

    # this field stores Amazon processing status.
    # when it is done, the sync status changes to
    # one of the final status.
    amazon_message_code = fields.Char(
        string='Amazon Result Message Code',
        index=True,
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
