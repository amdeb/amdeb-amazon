# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from ..shared.model_names import (
    AMAZON_PRODUCT_SYNC_TABLE,
    PRODUCT_CREATE_DATE_FIELD, SYNC_STATUS_FIELD,
    SYNC_CHECK_STATUS_COUNT_FILED, AMAZON_MESSAGE_CODE_FIELD,
    AMAZON_RESULT_DESCRIPTION_FIELD,
)
from ..shared.sync_status import SYNC_STATUS_PENDING, SYNC_STATUS_ERROR

_logger = logging.getLogger(__name__)

_UNLINK_DAYS = 100
_ARCHIVE_DAYS = 5
_ARCHIVE_CHECK_COUNT = 100
_ARCHIVE_CODE = "Timeout"
_ARCHIVE_MESSAGE = "Pending more than {0} days and {1} checks".format(
    _ARCHIVE_DAYS, _ARCHIVE_CHECK_COUNT
)


class ProductSyncChore(object):
    def __init__(self, env):
        self._table = env[AMAZON_PRODUCT_SYNC_TABLE]

    def archive_pending(self):
        _logger.debug("Enter ProductSyncChore archive_pending()")
        now = datetime.utcnow()
        archive_date = now - timedelta(days=_ARCHIVE_DAYS)
        archive_date_str = archive_date.strftime(DATETIME_FORMAT)
        archive_records = self._table.search([
            (PRODUCT_CREATE_DATE_FIELD, '<', archive_date_str),
            (SYNC_STATUS_FIELD, '=', SYNC_STATUS_PENDING),
            (SYNC_CHECK_STATUS_COUNT_FILED, '>=', _ARCHIVE_CHECK_COUNT)
        ])
        if archive_records:
            archive_status = {
                SYNC_STATUS_FIELD: SYNC_STATUS_ERROR,
                AMAZON_MESSAGE_CODE_FIELD: _ARCHIVE_CODE,
                AMAZON_RESULT_DESCRIPTION_FIELD: _ARCHIVE_MESSAGE
            }
            archive_records.write(archive_status)
        count = len(archive_records)
        _logger.debug("Archived {} timeout amazon sync records".format(
            count
        ))

    def cleanup(self):
        _logger.debug("Enter ProductSyncAccess cleanup()")
        now = datetime.utcnow()
        unlink_date = now - timedelta(days=_UNLINK_DAYS)
        unlink_date_str = unlink_date.strftime(DATETIME_FORMAT)
        unlink_records = self._table.search([
            (PRODUCT_CREATE_DATE_FIELD, '<', unlink_date_str)
        ])
        count = len(unlink_records)
        if unlink_records:
            unlink_records.unlink()

        log_template = "Cleaned {} ancient amazon sync records."
        _logger.debug(log_template.format(count))
