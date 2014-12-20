# -*- coding: utf-8 -*-

from datetime import date
import logging

from ...models_access import ProductSyncAccess

_last_chore_date = None
_logger = logging.getLogger(__name__)


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
        _logger.debug("Time to run daily chore for product sync.")
        _last_chore_date = current_day
        product_sync = ProductSyncAccess(env)

        product_sync.cleanup()
        product_sync.archive_old()
