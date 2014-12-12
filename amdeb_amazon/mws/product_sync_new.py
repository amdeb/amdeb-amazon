# -*- coding: utf-8 -*-

# import cPickle

# from .connector import Boto
from ..shared.model_names import (
    # PRODUCT_TEMPLATE,
    # PRODUCT_PRODUCT,
    # AMAZON_SYNC_TIMESTAMP_FIELD,
    AMAZON_PRODUCT_SYNC_TABLE,
    SYNC_STATUS_FIELD,
    SYNC_TYPE_FIELD,
)
from ..shared.sync_operation_types import (
    # SYNC_CREATE,
    SYNC_UPDATE,
    # SYNC_DELETE,
    # SYNC_PRICE,
    # SYNC_INVENTORY,
    # SYNC_IMAGE,
    # SYNC_DEACTIVATE,
)
from ..shared.sync_status import (
    SYNC_NEW,
    # SYNC_PENDING,
)


class ProductSyncNew(object):
    """This class processes new sync operations"""
    def __init__(self, env):
        self.env = env
        self.amazon_sync = self.env[AMAZON_PRODUCT_SYNC_TABLE]

    def _get_updates(self):
        search_domain = [
            (SYNC_STATUS_FIELD, '=', SYNC_NEW),
            (SYNC_TYPE_FIELD, '=', SYNC_UPDATE)
        ]
        self.updates = self.amazon_sync.search(search_domain)

    def _sync_update(self):
        self._get_updates()


    def synchronize(self):
        self._sync_update()
