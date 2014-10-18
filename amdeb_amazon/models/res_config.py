# -*- coding: utf-8 -*-

from openerp import models, fields


class Configuration(models.TransientModel):
    _name = 'amdeb.amazon.config.settings'
    _inherit = 'res.config.settings'

    default_account_id = fields.Char(
        string='Account Id',
        required=True,
        help="The Amazon Merchant Identifier",
        default_model='amdeb.amazon.config.settings',
    )

    default_access_key = fields.Char(
        string='Access Key',
        required=True,
        help="The Amazon Marketplace Web Service (MWS) access key",
        default_model='amdeb.amazon.config.settings',
    )

    default_secrete_key = fields.Char(
        string='Secret Key',
        required=True,
        help="The Amazon Marketplace Web Service (MWS) secret key",
        default_model='amdeb.amazon.config.settings',
    )

    default_integration_interval = fields.Integer(
        string='Integration Interval (seconds)',
        required=True,
        default=60,
        help="The minimum interval for Amazon automatic integration",
        default_model='amdeb.amazon.config.settings',
    )

    default_automatic_flag = fields.Boolean(
        string='Automatic Integration',
        default=True,
        help="Enable or disable Amazon automatic integration",
        default_model='amdeb.amazon.config.settings',
    )
