# -*- coding: utf-8 -*-

import logging


class Event(object):
    """
    Store a model and its subscribers as a dictionary entry.
    Subscribers of a model are stored in a set.
    """

    _logger = logging.getLogger(__name__)

    def __init__(self, event_name):
        self.name = event_name
        self._model_dict = {}
        Event._logger.info("Event {} is created.".format(self.name))

    def subscribe(self, model_name, subscriber):
        Event._logger.info(
            "Event {} subscribes {} for model {}".format(
                self.name, subscriber, model_name
            )
        )

        if model_name in self._model_dict:
            self._model_dict[model_name].add(subscriber)
        else:
            self._model_dict[model_name] = {subscriber}

    def fire(self, model_name, *args, **kwargs):
        Event._logger.debug(
            "Event {} fires for model {}".format(self.name, model_name)
        )

        if model_name in self._model_dict:
            subscribers = self._model_dict[model_name]
            for subscriber in subscribers:
                Event._logger.debug(
                    "Event {} calls {} for model {}. args: {}, "
                    "kwargs: {}.".format(
                        self.name, subscriber, model_name, args, kwargs
                    )
                )
                subscriber(model_name, *args, **kwargs)

    def __call__(self, model_name):
        """ decorator syntax for subscribing an event """
        def wrapper(subscriber):
            self.subscribe(model_name, subscriber)
            return subscriber
        return wrapper

create_record_event = Event("create_record_event")
write_record_event = Event("write_record_event")
unlink_record_event = Event("unlink_record_event")
