# -*- coding: utf-8 -*-

from openerp import models, fields

from ..shared.model_names import (
    PRODUCT_TEMPLATE,
)


class product_template(models.Model):
    _inherit = [PRODUCT_TEMPLATE]

    amazon_sync_active = fields.Boolean(
        string="Amazon Synchronization Active Flag",
        related='product_variant_ids.amazon_sync_active',
    )

    amazon_image_trigger = fields.Boolean(
        string="Amazon Image Synchronization Trigger",
        related='product_variant_ids.amazon_image_trigger',
    )

    amazon_asin = fields.Char(
        string="Amazon Product ASIN Number",
        related='product_variant_ids.amazon_asin',
    )

    amazon_bullet_point1 = fields.Char(
        string="Amazon Bullet Point 1",
        related='product_variant_ids.amazon_bullet_point1',
    )

    amazon_bullet_point2 = fields.Char(
        string="Amazon Bullet Point 2",
        related='product_variant_ids.amazon_bullet_point2',
    )

    amazon_bullet_point3 = fields.Char(
        string="Amazon Bullet Point 3",
        related='product_variant_ids.amazon_bullet_point3',
    )

    amazon_bullet_point4 = fields.Char(
        string="Amazon Bullet Point 4",
        related='product_variant_ids.amazon_bullet_point4',
    )

    amazon_bullet_point5 = fields.Char(
        string="Amazon Bullet Point 5",
        related='product_variant_ids.amazon_bullet_point5',
    )
