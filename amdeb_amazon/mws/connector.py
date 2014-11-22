# -*- coding: utf-8 -*-

import jinja2
import logging
import time

from boto.mws import connection

MarketPlaceID = 'ATVPDKIKX0DER'
_logger = logging.getLogger(__name__)


class Boto(object):
    def __init__(self, settings):
        loader = jinja2.PackageLoader(
            'openerp.addons.amdeb_amazon', "mws_templates")
        env = jinja2.Environment(loader=loader, autoescape=True,
                                 trim_blocks=True, lstrip_blocks=True)
        self.template = env.get_template('product_feed_template.xml')
        self.merchant_id = settings['account_id']

        self.conn = connection.MWSConnection(
            aws_access_key_id=settings['access_key'],
            aws_secret_access_key=settings['secret_key'],
            Merchant=self.merchant_id)

    def send(self, values):
        namespace = dict(MerchantId=self.merchant_id, FeedMessages=values)
        feed_content = self.template.render(namespace).encode('utf-8')

        feed = self.conn.submit_feed(
            FeedType='_POST_PRODUCT_DATA_',
            PurgeAndReplace=False,
            MarketplaceIdList=[MarketPlaceID],
            content_type='text/xml',
            FeedContent=feed_content
        )

        feed_info = feed.SubmitFeedResult.FeedSubmissionInfo
        _logger.debug(str(feed_info))

        while True:
            submission_list = self.conn.get_feed_submission_list(
                FeedSubmissionIdList=[feed_info.FeedSubmissionId]
            )
            list_result = submission_list.GetFeedSubmissionListResult
            info = list_result.FeedSubmissionInfo[0]
            id = info.FeedSubmissionId
            status = info.FeedProcessingStatus
            _logger.debug('Submission Id: {}. Current status: {}'.format(
                id, status))

            if (status in ('_SUBMITTED_', '_IN_PROGRESS_', '_UNCONFIRMED_')):
                _logger.debug('Sleeping and check again....')
                time.sleep(60)
            elif (status == '_DONE_'):
                feedResult = self.conn.get_feed_submission_result(
                    FeedSubmissionId=id)
                _logger.debug(str(feedResult))
                break
            else:
                _logger.warning("Submission processing error. Quit.")
                break

        return status
