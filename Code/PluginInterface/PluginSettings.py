
from ..Util.DebugObject import DebugObject

class BasePluginSetting(object):

    """ Base class for all plugin settings """

    def __init__(self, runtime=False):
        self._runtime = False
        self._value = None

    def is_runtime(self):
        """ Returns whether the settings contains a value which can be
        changed at runtime """
        return self._runtime

    def get_value(self):
        """ Returns the value of the setting """
        return self._value


class PluginSettingInt(BasePluginSetting):

    """ A setting storing a single integer """

    def __init__(self, min_value=0, max_value=10000, value=None, runtime=False):
        assert(min_value <= max_value)
        BasePluginSetting.__init__(self, runtime)        
        self._min_value = min_value
        self._max_value = max_value
        self._value = value if value is not None else self._min_value
        assert(self._value >= min_value and self._value <= max_value)

    def get_min_value(self):
        return self._min_value

    def get_max_value(self):
        return self._max_value

    def set_value(self, val):
        self._value = max(min(int(val), self._max_value), self._min_value)


class PluginSettingFloat(BasePluginSetting):

    """ A setting storing a single float """

    def __init__(self, min_value=0.0, max_value=10000.0, value=None, runtime=False):
        assert(min_value <= max_value)
        BasePluginSetting.__init__(self, runtime)
        self._min_value = min_value
        self._max_value = max_value
        self._value = value if value is not None else self._min_value
        assert(self._value >= min_value and self._value <= max_value)

    def get_min_value(self):
        return self._min_value

    def get_max_value(self):
        return self._max_value

    def set_value(self, val):
        self._value = max(min(float(val), self._max_value), self._min_value)


class PluginSettingEnum(BasePluginSetting):

    def __init__(self, *args, **kwargs):
        assert(len(args) > 0)
        runtime = "runtime" in kwargs and kwargs["runtime"]
        value = kwargs["value"] if "value" in kwargs else 0
        BasePluginSetting.__init__(self, runtime)
        self._enum_values = args
        self._value = 0
        if value is not None:
            if value not in self._enum_values:
                DebugObject.global_warn("PluginSettingEnum",
                    "Warning: ", value, "is not contained in the enum!")
            else:
                self._value = self._enum_values.index(value)

    def get_enum_values(self):
        """ Returns all possible values of the enum """
        return self._enum_values




