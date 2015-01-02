# -*- coding: utf-8 -*-

from openerp import models, fields, api

from ..shared.model_names import AMAZON_SETTINGS_TABLE

_IR_CRON_XMLID = 'amdeb_amazon.ir_cron_amazon_sync'
_INTERVAL_NUMBER_FIELD = 'interval_number'
_ACTIVE_FIELD = 'active'


class Configuration(models.TransientModel):
    _name = AMAZON_SETTINGS_TABLE
    _inherit = 'res.config.settings'

    default_merchant_id = fields.Char(
        string='Merchant Id',
        required=True,
        help="The Amazon Merchant Identifier",
        default_model=AMAZON_SETTINGS_TABLE,
    )

    default_access_key = fields.Char(
        string='Access Key',
        required=True,
        help="The Amazon MWS access key",
        default_model=AMAZON_SETTINGS_TABLE,
    )

    default_secret_key = fields.Char(
        string='Secret Key',
        required=True,
        help="The Amazon MWS secret key",
        default_model=AMAZON_SETTINGS_TABLE,
    )

    default_synchronization_interval = fields.Integer(
        string='Synchronization Interval (minutes)',
        required=True,
        default=10,
        help="The minimum interval for Amazon automatic synchronization",
        default_model=AMAZON_SETTINGS_TABLE,
    )

    default_image_location = fields.Char(
        string='Product Image Location',
        required=True,
        default_model=AMAZON_SETTINGS_TABLE,
    )

    default_active_flag = fields.Boolean(
        string='Active Flag',
        # set to False thus not run before configuration is done
        default=False,
        help="Enable or disable Amazon automatic integration",
        default_model=AMAZON_SETTINGS_TABLE,
    )

    # set cron job interval and active status
    def set_settings(self, cr, uid, ids, context):
        env = api.Environment(cr, uid, context)
        cron_record = env.ref(_IR_CRON_XMLID)

        config = self.browse(cr, uid, ids[0], context)
        interval = config.default_synchronization_interval
        active = config.default_active_flag
        values = {_INTERVAL_NUMBER_FIELD: interval,
                  _ACTIVE_FIELD: active, }
        cron_record.write(values)
