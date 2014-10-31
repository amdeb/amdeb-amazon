# -*- coding: utf-8 -*-

import unittest2
from mock import Mock

from ..integrator.event import Event

# the filename has to be test_XXX to be executed by Odoo testing
# the class name doesn't matter
class TestEvent(unittest2.TestCase):

    def setUp(self):
        self.event = Event()
        self.model_name = 'test_model'
        self.subscriber = Mock(name='test_subscriber', return_value=None)
        self.model_name2 = 'test_model2'
        self.subscriber2 = Mock(name='test_subscriber2', return_value=None)
        self.event_arg = 'test_event_arg'

    def test_subscribe(self):
        """ A matched subscriber is called when an event fires """
        self.event.subscribe(self.model_name, self.subscriber)
        self.event.fire(self.model_name, self.event_arg)
        self.subscriber.assert_called_once_with(
            self.model_name,
            self.event_arg)

    def test_subscribe_multi_models(self):
        """ Subscribers called on multiple models """
        self.event.subscribe(self.model_name, self.subscriber)
        self.event.fire(self.model_name, self.event_arg)
        self.event.subscribe(self.model_name2, self.subscriber2)
        self.event.fire(self.model_name2, self.event_arg)

        self.subscriber.assert_called_once_with(
            self.model_name,
            self.event_arg)

        self.subscriber2.assert_called_once_with(
            self.model_name2,
            self.event_arg)

    def test_subscribe_multi_subscribers(self):
        """ Multiple subscribers of a model are called """
        self.event.subscribe(self.model_name, self.subscriber)
        self.event.subscribe(self.model_name, self.subscriber2)
        self.event.fire(self.model_name, self.event_arg)

        self.subscriber.assert_called_once_with(
            self.model_name,
            self.event_arg)

        self.subscriber2.assert_called_once_with(
            self.model_name,
            self.event_arg)
