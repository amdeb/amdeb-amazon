# -*- coding: utf-8 -*-

from openerp import api, models, fields
from openerp.exceptions import ValidationError

from ..model_names.shared_names import(
    SHARED_NAME_FIELD, MODEL_NAME_FIELD,
    RECORD_ID_FIELD, PRODUCT_SKU_FIELD,
)
from ..models_access.amazon_product_access import AmazonProductAccess
from ..model_names.product_product import (
    PRODUCT_PRODUCT_TABLE,
    AMAZON_SYNC_ACTIVE_FIELD,
    PRODUCT_TEMPLATE_ID_FIELD,
    PRODUCT_ATTRIBUTE_VALUE_IDS_FIELD,
)
from ..model_names.product_template import (
    PRODUCT_TEMPLATE_TABLE,
    PRODUCT_AMAZON_DESCRIPTION_FIELD,
)


class ProductProduct(models.Model):
    _inherit = [PRODUCT_PRODUCT_TABLE]

    def _get_creation_status(self):
        sync_head = {}
        # if it is a partial variant, check its template
        if self[PRODUCT_ATTRIBUTE_VALUE_IDS_FIELD]:
            sync_head[MODEL_NAME_FIELD] = PRODUCT_PRODUCT_TABLE
            sync_head[RECORD_ID_FIELD] = self.id
        else:
            sync_head[MODEL_NAME_FIELD] = PRODUCT_TEMPLATE_TABLE
            sync_head[RECORD_ID_FIELD] = self[PRODUCT_TEMPLATE_ID_FIELD].id

        amazon_product = AmazonProductAccess(self.env)
        return amazon_product.get_creation_status(sync_head)

    amazon_creation_status = fields.Char(
        string="Amazon Creation Status",
        help="A status code showing whether this product creation status "
             "is waiting, created or error.",
        compute=_get_creation_status,
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
            missing_fields = []
            if not template[SHARED_NAME_FIELD]:
                has_error = True
                missing_fields.append(SHARED_NAME_FIELD)
            if not record[PRODUCT_SKU_FIELD]:
                has_error = True
                missing_fields.append(PRODUCT_SKU_FIELD)
            if not template[PRODUCT_AMAZON_DESCRIPTION_FIELD]:
                has_error = True
                missing_fields.append(PRODUCT_AMAZON_DESCRIPTION_FIELD)
            if has_error:
                missing_fields = ', '.join(missing_fields)
                raise ValidationError(message + missing_fields)
