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
        self._jj2_env = jinja2.Environment(
            loader=loader, autoescape=True,
            trim_blocks=True, lstrip_blocks=True)

        self._merchant_id = settings['merchant_id']
        self._image_location = settings['image_location']
        self.conn = connection.MWSConnection(
            aws_access_key_id=settings['access_key'],
            aws_secret_access_key=settings['secret_key'],
            Merchant=self._merchant_id)

    def _send(self, feed_type, template_name, values):
        """
        send MWS request and return feed id, feed time and feed status
        """
        _logger.debug("Boto send type: {0}, data: {1}".format(
            feed_type, values))
        namespace = {
            'MerchantId': self._merchant_id,
            'FeedMessages': values,
            'ImageLocation': self._image_location,
        }

        template = self._jj2_env.get_template(template_name)
        feed_content = template.render(namespace).encode('utf-8')
        _logger.debug("Boto feed content: {}".format(feed_content))

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
            feed_id, feed_time, feed_status))

        return feed_id, feed_time, feed_status

    def send_product(self, values):
        return self._send('_POST_PRODUCT_DATA_', 'product.jj2', values)

    def send_delete(self, values):
        return self._send('_POST_PRODUCT_DATA_', 'product_delete', values)

    def send_price(self, values):
        return self._send('_POST_PRODUCT_PRICING_DATA_',
                          'product_price.jj2', values)

    def send_inventory(self, values):
        return self._send('_POST_INVENTORY_AVAILABILITY_DATA_',
                          'product_inventory.jj2', values)

    def send_image(self, values):
        return self._send('_POST_PRODUCT_IMAGE_DATA_',
                          'product_image.jj2', values)

    def send_relation(self, values):
        return self._send('_POST_PRODUCT_RELATIONSHIP_DATA_ ',
                          'product_relation.jj2', values)

    @staticmethod
    def _get_submission_list_result(submission_list, sync_status):
        list_result = submission_list.GetFeedSubmissionListResult
        for info in list_result.FeedSubmissionInfo:
            submission_id = info.FeedSubmissionId
            status = info.FeedProcessingStatus
            _logger.debug('Submission Id: {}. Current status: {}'.format(
                submission_id, status))
            sync_status[submission_id] = status

    def check_sync_status(self, submission_id_list):
        sync_status = {}
        # iter_call handles pagination, stop and return result when
        # any exception happens
        try:
            # has to use the capitalized method name due to a boto bug
            for submission_list in self.conn.iter_call(
                    'GetFeedSubmissionList',
                    FeedSubmissionIdList=submission_id_list):
                Boto._get_submission_list_result(
                    submission_list, sync_status)
        except:
            _logger.exception("Exception in mws check_sync_status.")

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

        """
        feed_result = self.conn.get_feed_submission_result(
            FeedSubmissionId=submission_id)
        return _parse_sync_result(feed_result)
