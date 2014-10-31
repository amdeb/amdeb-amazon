# -*- coding: utf-8 -*-

from unittest2 import TestCase
from mock import Mock

# use absolute import for PyCharm, relative import for Odoo
if '.' not in __name__:
    from amdeb_amazon.integrator.event import Event
else:
    from ..integrator.event import Event


# the filename has to be test_XXX to be executed by Odoo testing
# the class name doesn't have this convention
class TestEvent(TestCase):

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

    def test_event_decorator(self):
        """ subscribe using event decorator """
        @self.event(self.model_name)
        def subscriber(model_name, event_arg):
            mock = self.subscriber
            mock(model_name, event_arg)

        self.event.fire(self.model_name, self.event_arg)
        self.subscriber.assert_called_once_with(
            self.model_name,
            self.event_arg)

    def test_subscribe_different_models(self):
        """ Different subscribers for different models """
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
        """ Multiple subscribers for a model """
        self.event.subscribe(self.model_name, self.subscriber)
        self.event.subscribe(self.model_name, self.subscriber2)
        self.event.fire(self.model_name, self.event_arg)

        self.subscriber.assert_called_once_with(
            self.model_name,
            self.event_arg)

        self.subscriber2.assert_called_once_with(
            self.model_name,
            self.event_arg)
