# -*- coding: utf-8 -*-

from ..shared.model_names import(
    MODEL_NAME_FIELD,
    RECORD_ID_FIELD,
)


class ProductUtility(object):
    def __init__(self, env):
        self._env = env

    def is_existed(self, header):
        model_name = header[MODEL_NAME_FIELD]
        record_id = header[RECORD_ID_FIELD]
        table = self._env[model_name]
        return bool(table.browse(record_id).exists())
