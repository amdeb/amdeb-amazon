# -*- coding: utf-8 -*-
from ..model_names.amazon_setting import (
    IR_VALUES_TABLE, AMAZON_SETTINGS_TABLE,
)


class ResConfigAccess(object):
    @staticmethod
    def get_settings(env):
        ir_values = env[IR_VALUES_TABLE]
        settings = ir_values.get_defaults_dict(AMAZON_SETTINGS_TABLE)
        return settings
