# -*- coding: utf-8 -*-

from openerp import models, fields

from ..shared.model_names import PRODUCT_TEMPLATE_TABLE


class product_template(models.Model):
    _inherit = [PRODUCT_TEMPLATE_TABLE]

    # we don't care about the product 'active' field
    amazon_sync_active = fields.Boolean(
        string="Amazon Synchronization Active Flag",
        related='product_variant_ids.amazon_sync_active',
    )

    brand = fields.Char(
        string="Product Brand",
        related='product_variant_ids.brand',
    )

    description_text = fields.Text(
        string="Plain Text Product Description",
        related='product_variant_ids.description_text',
    )

    image_path = fields.Char(
        string="HTTP Path Prefix of Product Images",
        help="HTTP path prefix without a trailing / for product images. "
             "Image names use a pattern that main image is SKU_main.jpg, "
             "other names are from  SKU_1.jpg to SKU_9.jpg. "
             "SKU represents the product SKU number.",
        related='product_variant_ids.image_path',
    )

    amazon_image_trigger = fields.Boolean(
        string="Amazon Image Synchronization Trigger",
        help="Changing this value triggers Amazon image synchronization.",
        related='product_variant_ids.amazon_image_trigger',
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
