# -*- coding: utf-8 -*-

from openerp import models, fields


class Configuration(models.Model):
    _name = 'amdeb.amazon.configuration'
    _description = 'Amdeb Amazon integration configuration'

    account_id = fields.Char(
        string='Account Id',
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
        string="Automatic Integration",
        required=True,
        default=True,
    )
