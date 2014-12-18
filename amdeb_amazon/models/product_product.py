# -*- coding: utf-8 -*-

from openerp import models, fields

from ..shared.model_names import (
    PRODUCT_PRODUCT_TABLE,
)


class product_product(models.Model):
    _inherit = [PRODUCT_PRODUCT_TABLE]

    # we don't care about the product 'active' field
    amazon_sync_active = fields.Boolean(
        string="Amazon Sync Active Flag",
        default=True,
    )

    amazon_image_trigger = fields.Boolean(
        string="Amazon Image Sync Trigger",
        help="Changing this value triggers Amazon image synchronization.",
        default=False,
    )

    amazon_bullet_point1 = fields.Char(
        string="Amazon Bullet Point 1"
    )

    amazon_bullet_point2 = fields.Char(
        string="Amazon Bullet Point 2"
    )

    amazon_bullet_point3 = fields.Char(
        string="Amazon Bullet Point 3"
    )

    amazon_bullet_point4 = fields.Char(
        string="Amazon Bullet Point 4"
    )

    amazon_bullet_point5 = fields.Char(
        string="Amazon Bullet Point 5"
    )
