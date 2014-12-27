# -*- coding: utf-8 -*-

from openerp import models, fields

from ..shared.model_names import PRODUCT_PRODUCT_TABLE


class product_product(models.Model):
    _inherit = [PRODUCT_PRODUCT_TABLE]

    # we don't care about the product 'active' field
    # set default to False to let use fill all data and
    # start sync
    amazon_sync_active = fields.Boolean(
        string="Amazon Sync Active Flag",
        default=False,
    )

    brand = fields.Char(
        string="Product Brand"
    )

    description_text = fields.Text(
        string="Plain Text Product Description"
    )

    image_path = fields.Char(
        string="HTTP Path Prefix of Product Images",
        help="HTTP path prefix without a trailing / for product images. "
             "Image names use a pattern that main image is SKU_main.jpg, "
             "other names are from  SKU_1.jpg to SKU_9.jpg. "
             "SKU represents the product SKU number.",
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
