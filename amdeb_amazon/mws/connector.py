# -*- coding: utf-8 -*-

import jinja2
import logging

from boto.mws import connection

MarketPlaceID = 'ATVPDKIKX0DER'
_logger = logging.getLogger(__name__)

from ..shared.model_names import (
    IR_VALUES,
    AMAZON_SETTINGS_TABLE,
)


class Boto(object):
    def __init__(self, odoo_env):
        ir_values = odoo_env[IR_VALUES]
        settings = ir_values.get_defaults_dict(AMAZON_SETTINGS_TABLE)

        loader = jinja2.PackageLoader(
            'openerp.addons.amdeb_amazon', "mws_templates")
        env = jinja2.Environment(loader=loader, autoescape=True,
                                 trim_blocks=True, lstrip_blocks=True)
        self.template = env.get_template('product_feed_template.xml')
        self.merchant_id = settings['merchant_id']

        self.conn = connection.MWSConnection(
            aws_access_key_id=settings['access_key'],
            aws_secret_access_key=settings['secret_key'],
            Merchant=self.merchant_id)

    def send(self, values):
        _logger.debug("Boto send data: {}", values)
        namespace = dict(MerchantId=self.merchant_id, FeedMessages=values)
        feed_content = self.template.render(namespace).encode('utf-8')

        response = self.conn.submit_feed(
            FeedType='_POST_PRODUCT_DATA_',
            PurgeAndReplace=False,
            MarketplaceIdList=[MarketPlaceID],
            content_type='text/xml',
            FeedContent=feed_content
        )

        feed_info = response.SubmitFeedResult.FeedSubmissionInfo
        _logger.debug("Boto submit feed result: {}", feed_info)

        feed_id = feed_info.FeedSubmissionId
        feed_time = feed_info.SubmittedDate
        feed_status = feed_info.FeedProcessingStatus
        return feed_id, feed_time, feed_status

    def check_sync_status(self, submission_id_list):
        status_list = {}

        # ToDo: handle pagination
        submission_list = self.conn.get_feed_submission_list(
            FeedSubmissionIdList=submission_id_list
        )
        list_result = submission_list.GetFeedSubmissionListResult
        for info in list_result.FeedSubmissionInfo:
            submission_id = info.FeedSubmissionId
            status = info.FeedProcessingStatus
            _logger.debug('Submission Id: {}. Current status: {}'.format(
                submission_id, status))
            status_list[submission_id] = status

        return status_list

    def get_sync_result(self, submission_id):
        feed_result = self.conn.get_feed_submission_result(
            FeedSubmissionId=submission_id)
        _logger.debug(str(feed_result))
