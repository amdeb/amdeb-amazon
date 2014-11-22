# -*- coding: utf-8 -*-

from openerp import models, fields, api

from ..shared.model_names import (
    AMAZON_SETTINGS_TABLE,
    IR_CRON,
)

IR_CRON_XMLID = 'amdeb_amazon.ir_cron_amazon_sync'


class Configuration(models.TransientModel):
    _name = AMAZON_SETTINGS_TABLE
    _inherit = 'res.config.settings'

    default_account_id = fields.Char(
        string='Account Id',
        required=True,
        help="The Amazon Merchant Identifier",
        default_model=AMAZON_SETTINGS_TABLE,
    )

    default_access_key = fields.Char(
        string='Access Key',
        required=True,
        help="The Amazon Marketplace Web Service (MWS) access key",
        default_model=AMAZON_SETTINGS_TABLE,
    )

    default_secrete_key = fields.Char(
        string='Secret Key',
        required=True,
        help="The Amazon Marketplace Web Service (MWS) secret key",
        default_model=AMAZON_SETTINGS_TABLE,
    )

    default_synchronization_interval = fields.Integer(
        string='Synchronization Interval (minutes)',
        required=True,
        default=10,
        help="The minimum interval for Amazon automatic synchronization",
        default_model=AMAZON_SETTINGS_TABLE,
    )

    default_automatic_flag = fields.Boolean(
        string='Automatic Integration',
        default=True,
        help="Enable or disable Amazon automatic integration",
        default_model=AMAZON_SETTINGS_TABLE,
    )

    # set cron job interval
    def set_synchronization_interval(self, cr, uid, ids, context):
        env = api.Environment(cr, uid, context)
        cron_record = env.ref(IR_CRON_XMLID)

        config = self.browse(cr, uid, ids[0], context)
        interval = config.default_synchronization_interval
        cron_record.write({"interval_number": interval})
