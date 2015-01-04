# -*- coding: utf-8 -*-

from openerp import models, fields

from ..models_access.amazon_product_access import AmazonProductAccess
from ..shared.model_names import (
    PRODUCT_TEMPLATE_TABLE, MODEL_NAME_FIELD, RECORD_ID_FIELD,
)


class product_template(models.Model):
    _inherit = [PRODUCT_TEMPLATE_TABLE]

    def _is_created_amazon(self):
        model_id = {
            MODEL_NAME_FIELD: PRODUCT_TEMPLATE_TABLE,
            RECORD_ID_FIELD: self.ids[0],
        }

        amazon_product = AmazonProductAccess(self.env)
        return amazon_product.is_created(model_id)

    amazon_created = fields.Boolean(
        string="Is Created in Amazon",
        help="A readonly flag showing whether this product is created "
             "in Amazon or not.",
        compute=_is_created_amazon,
        readonly=True,
    )

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

    amazon_description = fields.Text(
        string="Amazon Product Description",
        help="Product description in Amazon. If empty, sales description "
             "will be used."
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
