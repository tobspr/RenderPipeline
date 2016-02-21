"""

RenderPipeline

Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

from rplibs.six import iteritems
from rpcore.rp_object import RPObject

__all__ = ["make_setting_from_data"]

def make_setting_from_data(data):
    """ Constructs a new setting from a given dataset. This method will automatically
    instantiate a new class matching the type of the given dataset. It will fill
    all values provided by the dataset and then return the created instance """
    factory = {
        "int": IntType,
        "float": FloatType,
        "bool": BoolType,
        "enum": EnumType,
        "path": PathType
    }
    if data["type"] not in factory:
        raise Exception("Unkown setting type: {}".format(data["type"]))
    instance = factory[data["type"]](data)
    if data:
        raise Exception("Unparsed data left in plugin setting: {}".format(data))
    return instance

class BaseType(RPObject):

    """ This is the base setting type, all setting types derive from this """

    def __init__(self, data):
        """ Fills in all settings from the given setting data """
        self.value = None
        self.type = data.pop("type")
        self.label = data.pop("label").strip()
        self.description = data.pop("description").strip()
        self.runtime = data.pop("runtime", False)
        self.shader_runtime = data.pop("shader_runtime", False)
        self.display_conditions = data.pop("display_if", {})

        RPObject.__init__(self, "psetting:{}".format(self.label))

    def set_value(self, value):
        """ Sets the value of the setting, should get overridden """
        raise NotImplementedError()

    def write_defines(self, plugin_id, setting_id, definer):
        """ Makes the value of this plugin available as a define """
        definer("{}__{}".format(plugin_id, setting_id), self.value)

    def should_be_visible(self, settings):
        """ Evaluates whether the plugin should be visible, taking all display
        conditions into account """
        for key, val in iteritems(self.display_conditions):
            if settings[key].value != val:
                return False
        return True

class TemplatedType(BaseType):

    """ This setting stores a single type including a minimum and maximum value.
    It is shared between integer and floating point types. """

    def __init__(self, template_type, data):
        BaseType.__init__(self, data)
        self.template_type = template_type
        self.default = template_type(data.pop("default"))
        self.value = self.default

        setting_range = data.pop("range")
        self.minval = template_type(setting_range[0])
        self.maxval = template_type(setting_range[1])

    def set_value(self, value):
        value = self.template_type(value)
        if self.minval <= value <= self.maxval:
            self.value = value
        else:
            self.error("Invalid value: {}".format(value))

class IntType(TemplatedType):
    """ Template instantiation of TemplatedType using int """

    def __init__(self, data):
        TemplatedType.__init__(self, int, data)

class FloatType(TemplatedType):
    """ Template instantiation of TemplatedType using float """

    def __init__(self, data):
        TemplatedType.__init__(self, float, data)

class BoolType(BaseType):
    """ Boolean setting type """

    def __init__(self, data):
        BaseType.__init__(self, data)
        self.default = bool(data.pop("default"))
        self.value = self.default

    def set_value(self, value):
        self.value = bool(value)

class EnumType(BaseType):
    """ Enumeration setting type """
    def __init__(self, data):
        BaseType.__init__(self, data)
        self.values = tuple(data.pop("values"))
        self.default = data.pop("default")
        if self.default not in self.values:
            raise Exception("Enum default not in enum values: {}".format(self.default))
        self.value = self.default

    def set_value(self, value):
        if value not in self.values:
            self.error("Value not in enum values!")
            return
        self.value = value

    def write_defines(self, plugin_id, setting_id, definer):
        definer("{}__{}".format(plugin_id, setting_id), 1000 + self.values.index(self.value))

        for i, val in enumerate(self.values):
            definer("{}_ENUM_{}_{}".format(plugin_id, setting_id, val), 1000 + i)

class PathType(BaseType):
    """ Path type to specify paths to files """
    def __init__(self, data):
        BaseType.__init__(self, data)
        self.default = str(data.pop("default"))
        self.value = self.default

    def set_value(self, value):
        self.value = str(value)

    def write_defines(self, *args):
        # Paths are not available in shaders
        pass
