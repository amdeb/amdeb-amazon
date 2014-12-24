# -*- coding: utf-8 -*-

import jinja2
from lxml import etree
import logging

from boto.mws import connection

MarketPlaceID = 'ATVPDKIKX0DER'
_logger = logging.getLogger(__name__)


def _parse_sync_result(feed_result):
    # ToDo: depend on boto PR#2660 to return an XML doc
    completion_result = {}
    doc = etree.fromstring(feed_result)
    message = doc.find('Message')
    report = message.find('ProcessingReport')
    processed = report.find('ProcessingSummary/MessagesProcessed').text
    successful = report.find('ProcessingSummary/MessagesSuccessful').text
    processed_count = int(processed)
    successful_count = int(successful)
    if successful_count < processed_count:
        results = report.findall('Result')
        for result in results:
            message_id = int(result.find('MessageID').text)
            result_code = result.find('ResultCode').text
            result_message_code = result.find('ResultMessageCode')
            result_description = result.find('ResultDescription').text

            completion_result[message_id] = (
                result_code,
                result_message_code,
                result_description
            )

    _logger.debug("Submission results: {}".format(completion_result))
    return completion_result


class Boto(object):
    def __init__(self, settings):
        loader = jinja2.PackageLoader(
            'openerp.addons.amdeb_amazon', "mws_templates")
        self._env = jinja2.Environment(
            loader=loader, autoescape=True,
            trim_blocks=True, lstrip_blocks=True)

        self.merchant_id = settings['merchant_id']

        self.conn = connection.MWSConnection(
            aws_access_key_id=settings['access_key'],
            aws_secret_access_key=settings['secret_key'],
            Merchant=self.merchant_id)

    def _send(self, feed_type, template_name, values):
        """
        send MWS request and return feed id, feed time and feed status
        """
        _logger.debug("Boto send data: {}".format(values))
        namespace = dict(MerchantId=self.merchant_id, FeedMessages=values)
        template = self._env.get_template(template_name)
        feed_content = template.render(namespace).encode('utf-8')

        response = self.conn.submit_feed(
            FeedType=feed_type,
            PurgeAndReplace=False,
            MarketplaceIdList=[MarketPlaceID],
            content_type='text/xml',
            FeedContent=feed_content
        )
        feed_info = response.SubmitFeedResult.FeedSubmissionInfo
        feed_id = feed_info.FeedSubmissionId
        feed_time = feed_info.SubmittedDate
        feed_status = feed_info.FeedProcessingStatus

        logger_template = "Boto send result. Id: {0}, Time: {1},status {2}."
        _logger.debug(logger_template.format(
            feed_id, feed_time, feed_status
        ))
        return feed_id, feed_time, feed_status

    def send_product(self, values):
        return self._send('_POST_PRODUCT_DATA_ ', 'product.jj2', values)

    def send_price(self, values):
        return self._send('_POST_PRODUCT_PRICING_DATA_', 'price.jj2', values)

    def check_sync_status(self, submission_id_list):
        sync_status = {}

        # ToDo: handle pagination and return all results to make it simple
        submission_list = self.conn.get_feed_submission_list(
            FeedSubmissionIdList=submission_id_list
        )
        list_result = submission_list.GetFeedSubmissionListResult
        for info in list_result.FeedSubmissionInfo:
            submission_id = info.FeedSubmissionId
            status = info.FeedProcessingStatus
            _logger.debug('Submission Id: {}. Current status: {}'.format(
                submission_id, status))
            sync_status[submission_id] = status

        log_template = "Got {0} sync statuses for {1} submissions."
        _logger.debug(log_template.format(
            len(sync_status), len(submission_id_list)))
        return sync_status

    def get_sync_result(self, submission_id):
        """
        get feed submission processing result
        The result is a dict that use message id as a key.
        The value is a tuple of result code (Error or Warning),
        Amazon error/warning message code and description.

        :param submission_id: the feed submission id
        :return: warning and error results indexed by message id
        """
        feed_result = self.conn.get_feed_submission_result(
            FeedSubmissionId=submission_id)
        return _parse_sync_result(feed_result)
