# -*- coding: utf-8 -*-

from openerp import models, fields


class Course(models.Model):
    _name = 'amdeb.amazon.configuration'
    _description = 'Amdeb Amazon integration configuration'

    # default is the US marketplace Id
    marketplace_id = fields.Selection(
        (('ATVPDKIKX0DER', 'US Marketplace'),),
        string='Amazon Marketplace Id',
        required=True,
        default='US Marketplace',
    )

    account_id = fields.Char(
        string='Merchant Account Id',
        required=True,
    )

    access_key = fields.Char(
        string='Access Key',
        required=True,
    )

    secrete_key = fields.Char(
        string='Secret Key',
        required=True,
    )

    integration_interval = fields.Integer(
        string="Integration Interval (seconds)",
        required=True,
        default=60,
    )

    automatic_flag = fields.Boolean(
        string="Automatic Amazon Integration",
        required=True,
        default=True,
    )
