# -*- coding: utf-8 -*-

from ..shared.model_names import (
    AMAZON_PRODUCT_TABLE,
    MODEL_NAME_FIELD,
    RECORD_ID_FIELD,
)


class AmazonProductAccess(object):
    def __init__(self, env):
        self._amazon_product_table = env[AMAZON_PRODUCT_TABLE]

    def get_amazon_product(self, model_name, record_id):
        search_domain = [
            (MODEL_NAME_FIELD, '=', model_name),
            (RECORD_ID_FIELD, '=', record_id)
        ]
        amazon_product = self._amazon_product_table(search_domain)
        return amazon_product

    def is_created(self, model_name, record_id):
        return bool(self.get_amazon_product(model_name, record_id))
