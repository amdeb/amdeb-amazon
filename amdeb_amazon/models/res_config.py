# -*- coding: utf-8 -*-

from openerp import models, fields, api

from ..model_names.amazon_setting import AMAZON_SETTINGS_TABLE

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

    default_product_brand = fields.Char(
        string='Product Brand',
        help="This is the default value for product brand.",
        default_model=AMAZON_SETTINGS_TABLE,
    )

    default_amazon_department = fields.Char(
        string='Amazon Department',
        help="This is the default value for Amazon Product Department such"
             "as womens, mens, baby-boys etc found in an Amazon "
             "Browse Tree Guide (BTG) file.",
        default='womens',
        default_model=AMAZON_SETTINGS_TABLE,
    )

    default_amazon_item_type = fields.Char(
        string='Amazon Item Type',
        help="This is the default value for Amazon Product item type "
             "such as apparel-accessories, pants, handbags, etc found "
             "in an Amazon Browse Tree Guide (BTG) file.",
        default='handbags',
        default_model=AMAZON_SETTINGS_TABLE,
    )

    default_image_location = fields.Char(
        string='Product Image Location',
        required=True,
        help="The product image HTTP location without trailing slash. "
             "The location is public-accessible http (not https) url. Image "
             "name uses a pattern of SKU_main.jpg, SKU_1.jpg, "
             "SKU_2.jpg, ..., SKU_8.jpg. The SKU is the product SKU. "
             "Image size must be smaller than 10MB.",
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
