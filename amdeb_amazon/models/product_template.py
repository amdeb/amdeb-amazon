# -*- coding: utf-8 -*-

from openerp import models, fields

from ..shared.model_names import PRODUCT_TEMPLATE_TABLE


class product_template(models.Model):
    _inherit = [PRODUCT_TEMPLATE_TABLE]

    # we don't care about the product 'active' field
    amazon_sync_active = fields.Boolean(
        string="Amazon Synchronization Active Flag",
        help="Enable or disable Amazon product synchronization",
        related='product_variant_ids.amazon_sync_active',
    )

    amazon_image_trigger = fields.Boolean(
        string="Amazon Image Synchronization Trigger",
        help="Changing this value triggers Amazon image synchronization.",
        related='product_variant_ids.amazon_image_trigger',
    )

    brand = fields.Char(
        string="Product Brand",
    )

    description_text = fields.Text(
        string="Plain Text Product Description",
    )

    amazon_bullet_point1 = fields.Char(
        string="Amazon Bullet Point 1",
    )

    amazon_bullet_point2 = fields.Char(
        string="Amazon Bullet Point 2",
    )

    amazon_bullet_point3 = fields.Char(
        string="Amazon Bullet Point 3",
    )

    amazon_bullet_point4 = fields.Char(
        string="Amazon Bullet Point 4",
    )

    amazon_bullet_point5 = fields.Char(
        string="Amazon Bullet Point 5",
    )
