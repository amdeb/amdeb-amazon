# -*- coding: utf-8 -*-

import pickle

from .connector import Boto
from ..shared.model_names import (
    PRODUCT_OPERATION_TABLE,
    PRODUCT_TEMPLATE,
    PRODUCT_PRODUCT,
    IR_VALUES,
    AMAZON_SETTINGS_TABLE,
)
from ..shared.operations_types import (
    WRITE_RECORD,
)
from .product_operation_transformer import ProductOperationTransformer


class ProductSynchronization(object):
    def __init__(self, env):
        self.env = env
        self.product_operations = self.env[PRODUCT_OPERATION_TABLE]
        self.product_template = self.env[PRODUCT_TEMPLATE]
        self.product_product = self.env[PRODUCT_PRODUCT]

    def _get_mws(self):
        ir_values = self.env[IR_VALUES]
        settings = ir_values.get_defaults_dict(AMAZON_SETTINGS_TABLE)
        return Boto(settings)

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
        ''' synchronize product operations to Amazon

        There are several steps:
        1. convert new product operations to sync operations
        2. execute sync operations and update end timestamp
        3. get sync results for pending sync operations and update
        end timestamp
        4. create and execute new price, image and inventory sync
        operations for successful create sync operation
        '''
        transformer = ProductOperationTransformer(self.env)
        transformer.transform()
        # mws = self._get_mws()
        # self._sync_product(mws, operations)
