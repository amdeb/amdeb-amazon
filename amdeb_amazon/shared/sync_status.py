# -*- coding: utf-8 -*-

# the newly created status
SYNC_STATUS_NEW = 'New'

# a sync operation is waiting for amazon product creation
# the product sync active is True but Amazon created is False
SYNC_STATUS_WAITING = 'Waiting'

# mws class submitted status
SYNC_STATUS_PENDING = 'Pending'

# make sure the 'Success' and 'Warning' are the same values
# as the Amazon ResultCode returned from get_feed_submission_result
# Success means that there is no error, no warning
# Warning means minor issues
# Error means all kinds of errors: call failure, exception, Amazon error etc.
SYNC_STATUS_SUCCESS = 'Success'
SYNC_STATUS_WARNING = 'Warning'
SYNC_STATUS_ERROR = 'Error'

AMAZON_STATUS_PROCESS_DONE = '_DONE_'
