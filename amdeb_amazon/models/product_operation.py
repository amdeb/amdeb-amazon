# -*- coding: utf-8 -*-

from openerp import models, fields

from ..shared.model_names import PRODUCT_OPERATION_TABLE


class ProductOperation(models.Model):
    _name = PRODUCT_OPERATION_TABLE
    _description = 'Product Operation'
    _order = 'operation_timestamp'
    _log_access = False

    # don't use Many2One because we keep the record
    # even if the referred product is deleted
    record_id = fields.Integer(
        string='Record Id',
        required=True,
        index=True,
        readonly=True,
    )

    model_name = fields.Char(
        string='Model Name',
        required=True,
        readonly=True,
    )

    # the type of record operation such as create_record,
    # write_record or unlink_record
    record_operation = fields.Selection(
        string='Record Operation',
        required=True,
        selection=[('create_record', 'Create Record'),
                   ('write_record', 'Write Record'),
                   ('unlink_record', 'Unlink Record'),
                   ],
        readonly=True,
    )

    # the pickled record operation data
    # it is updating values in write
    # it is not set for create and unlink
    operation_data = fields.Binary(
        string='Operation Data',
        required=False,
        readonly=True,
    )

    operation_timestamp = fields.Datetime(
        string='Operation Timestamp',
        required=True,
        default=fields.Datetime.now(),
        readonly=True,
    )

    # the integration site name, some operations
    # are created only for a specific site.
    # by default, it is for all integration sites.
    site_name = fields.Char(
        string='Site Name',
        required=False,
        readonly=True,
    )
