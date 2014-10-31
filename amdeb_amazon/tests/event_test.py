# -*- coding: utf-8 -*-

import unittest2
import mock

from amdeb_amazon.event.event import Event


class EventTest(unittest2.TestCase):

    def setUp(self):
        self.event = Event()
        self.model_name = 'test_model'
        self.subscriber = mock.Mock(name='test_subscriber')
        self.event_arg = 'test_event_arg'

    def test_subscribe(self):
        self.event.subscribe(self.model_name, self.subscriber)
        self.event.fire(self.model_name, self.event_arg)
        self.subscriber.assert_called_once_with(
            self.model_name,
            self.event_arg)
