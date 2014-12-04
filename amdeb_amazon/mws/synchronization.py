# -*- coding: utf-8 -*-

import pickle

from .connector import Boto
from ..shared.model_names import (
    PRODUCT_OPERATION_TABLE,
    PRODUCT_TEMPLATE,
    PRODUCT_PRODUCT,
    IR_VALUES,
    AMAZON_SETTINGS_TABLE,
    OPERATION_AMAZON_STATUS_FIELD,
    WRITE_RECORD,
)
from ..shared.integration_status import (
    NEW_STATUS,
)


class Synchronization(object):
    # the eve is caller's environment
    def __init__(self, env):
        self.env = env
        self.product_operations = self.env[PRODUCT_OPERATION_TABLE]
        self.product_template = self.env[PRODUCT_TEMPLATE]
        self.product_product = self.env[PRODUCT_PRODUCT]

    def _get_mws(self):
        ir_values = self.env[IR_VALUES]
        settings = ir_values.get_defaults_dict(AMAZON_SETTINGS_TABLE)
        return Boto(settings)

    def _get_operations(self):
        search_domain = [(OPERATION_AMAZON_STATUS_FIELD, '=', NEW_STATUS), ]
        return self.product_operations.search(search_domain)

    def _sync_product(self, mws, operations):
        result = 'Empty Value Done'
        sync_values = []
        for operation in operations:
            if (operation.record_operation == WRITE_RECORD and
                    operation.model_name == PRODUCT_TEMPLATE):
                operation_data = pickle.loads(operation.operation_data)
                if 'name' in operation_data:
                    title = operation_data['name']
                    pt = self.product_template.browse(operation.record_id)
                    sku = pt.default_code
                    sync_value = {'SKU': sku, 'Title': title}
                    sync_values.append(sync_value)

        if sync_values:
            result = mws.send(sync_values)
        return result

    def synchronize(self):
        mws = self._get_mws()
        operations = self._get_operations()
        self._sync_product(mws, operations)
