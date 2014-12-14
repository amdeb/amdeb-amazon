# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, date
import logging
_logger = logging.getLogger(__name__)

from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

from ..shared.model_names import (
    AMAZON_PRODUCT_SYNC_TABLE,
    SYNC_CREATION_TIMESTAMP_FIELD,
    SYNC_STATUS_FIELD,
    SYNC_CHECK_STATUS_COUNT_FILED,
    AMAZON_MESSAGE_CODE_FIELD,
    AMAZON_RESULT_DESCRIPTION_FIELD
)

from ..shared.sync_status import (
    SYNC_PENDING,
    SYNC_ERROR,
)

_UNLINK_DAYS = 100
_ARCHIVE_MAGIC_NUMBER = 10
_ARCHIVE_CODE = "Timeout"
_ARCHIVE_MESSAGE = "Pending more than {0} days and checked {0} times".format(
    _ARCHIVE_MAGIC_NUMBER
)

_last_chore_date = None


def _cleanup(amazon_sync):
    _logger.debug("running product synchronization cleanup")
    now = datetime.utcnow()
    unlink_date = now - timedelta(days=_UNLINK_DAYS)
    unlink_date_str = unlink_date.strftime(DATETIME_FORMAT)
    unlink_records = amazon_sync.search([
        (SYNC_CREATION_TIMESTAMP_FIELD, '<', unlink_date_str)
    ])
    count = len(unlink_records)
    unlink_records.unlink()
    _logger.debug("deleted {} old amazon sync records".format(
        count
    ))


def _archive_old(amazon_sync):
    _logger.debug("running product synchronization archive")
    now = datetime.utcnow()
    archive_date = now - timedelta(days=_ARCHIVE_MAGIC_NUMBER)
    archive_date_str = archive_date.strftime(DATETIME_FORMAT)
    archive_records = amazon_sync.search([
        (SYNC_CREATION_TIMESTAMP_FIELD, '<', archive_date_str),
        (SYNC_STATUS_FIELD, '=', SYNC_PENDING),
        (SYNC_CHECK_STATUS_COUNT_FILED, '>=', _ARCHIVE_MAGIC_NUMBER)
    ])
    archive_status = {
        SYNC_STATUS_FIELD: SYNC_ERROR,
        AMAZON_MESSAGE_CODE_FIELD: _ARCHIVE_CODE,
        AMAZON_RESULT_DESCRIPTION_FIELD: _ARCHIVE_MESSAGE
    }
    archive_records.write(archive_status)
    count = len(archive_records)
    _logger.debug("archived {} old amazon sync records".format(
        count
    ))


def do_daily_chore(env):
    global _last_chore_date

    # run it when it starts the first time
    # or when the date changes
    run = False
    current_day = date.today()
    if _last_chore_date:
        diff = current_day - _last_chore_date
        if diff.days > 0:
            run = True
    else:
        run = True

    if run:
        _logger.debug("time to run daily chore...")
        _last_chore_date = current_day
        amazon_sync = env[AMAZON_PRODUCT_SYNC_TABLE]
        _cleanup(amazon_sync)
        _archive_old(amazon_sync)
