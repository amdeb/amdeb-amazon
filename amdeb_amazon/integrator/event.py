# -*- coding: utf-8 -*-


class Event():
    """
    Store a model and its subscribers as a dict entry.
    Subscribers of a model are stored in a set.
    """

    def __init__(self):
        self._model_dict = {}

    def subscribe(self, model_name, subscriber):
        if model_name in self._model_dict:
            self._model_dict[model_name].add(subscriber)
        else:
            self._model_dict[model_name] = {subscriber}

    def fire(self, model_name, *args, **kwargs):
        if model_name in self._model_dict:
            subscribers = self._model_dict[model_name]
            for subscriber in subscribers:
                subscriber(model_name, *args, **kwargs)

    def __call__(self, model_name):
        """ decorator syntax for subscribing an event """
        def wrapper(subscriber):
            self.subscribe(model_name, subscriber)
            return subscriber
        return wrapper
