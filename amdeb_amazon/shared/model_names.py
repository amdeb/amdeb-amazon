# -*- coding: utf-8 -*-

"""
contains definition of models names
"""

PRODUCT_TEMPLATE = 'product.template'
PRODUCT_PRODUCT = 'product.product'
IR_VALUES = 'ir.values'
IR_CRON = 'ir.cron'

PRODUCT_OPERATION_TABLE = 'amdeb.product.operation'
AMAZON_PRODUCT_SYNC_TABLE = 'amdeb.amazon.product.sync'
AMAZON_SETTINGS_TABLE = 'amdeb.amazon.config.settings'

AMAZON_SYNC_TIMESTAMP_FIELD = 'amazon_sync_timestamp'

# definition of integration table record operations
SYNC_CREATE = 'sync_create'
SYNC_UPDATE = 'sync_update'
SYNC_DELETE = 'sync_delete'
SYNC_PRICE = 'sync_price'
SYNC_INVENTORY = 'sync_inventory'
SYNC_IMAGE = 'sync_image'
SYNC_DEACTIVATE = 'sync_deactivate'
