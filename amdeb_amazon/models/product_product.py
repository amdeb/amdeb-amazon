# -*- coding: utf-8 -*-

from openerp import api, models, fields
from openerp.exceptions import ValidationError

from ..models_access.amazon_product_access import AmazonProductAccess

from ..shared.model_names import (
    PRODUCT_PRODUCT_TABLE,
    AMAZON_SYNC_ACTIVE_FIELD,
    PRODUCT_DEFAULT_CODE_FIELD,
    PRODUCT_NAME_FIELD,
    PRODUCT_TEMPLATE_ID_FIELD,
    PRODUCT_DESCRIPTION_SALE_FIELD,
    PRODUCT_AMAZON_DESCRIPTION_FIELD,
    MODEL_NAME_FIELD, RECORD_ID_FIELD,
)


class product_product(models.Model):
    _inherit = [PRODUCT_PRODUCT_TABLE]

    def _is_created_amazon(self):
        model_id = {
            MODEL_NAME_FIELD: PRODUCT_PRODUCT_TABLE,
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
    # set default to False to let use fill all data and
    # start sync
    amazon_sync_active = fields.Boolean(
        string="Amazon Sync Active Flag",
        help="Enable or disable Amazon product synchronization",
        default=False,
    )

    amazon_image_trigger = fields.Boolean(
        string="Amazon Image Synchronization Trigger",
        help="Changing this value triggers Amazon image synchronization.",
    )

    @api.constrains(AMAZON_SYNC_ACTIVE_FIELD)
    def _check_sync_fields(self):
        for record in self:
            if not record[AMAZON_SYNC_ACTIVE_FIELD]:
                continue
            template = record[PRODUCT_TEMPLATE_ID_FIELD]
            has_error = False
            message = 'Unable to enable sync because of missing value of: '
            if not template[PRODUCT_NAME_FIELD]:
                has_error = True
                message += ' ' + PRODUCT_NAME_FIELD
            if not record[PRODUCT_DEFAULT_CODE_FIELD]:
                has_error = True
                message += ' ' + PRODUCT_DEFAULT_CODE_FIELD
            if (not template[PRODUCT_DESCRIPTION_SALE_FIELD] and
                    not template[PRODUCT_AMAZON_DESCRIPTION_FIELD]):
                has_error = True
                message += (' ' + PRODUCT_DESCRIPTION_SALE_FIELD + ' or ' +
                            PRODUCT_AMAZON_DESCRIPTION_FIELD)
            if has_error:
                raise ValidationError(message)
