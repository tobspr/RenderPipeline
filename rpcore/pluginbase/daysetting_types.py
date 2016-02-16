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

from __future__ import division
from panda3d.core import PTAFloat, PTALVecBase3f

from ..rp_object import RPObject
from ..util.smooth_connected_curve import SmoothConnectedCurve

__all__ = ["make_daysetting_from_data"]

def make_daysetting_from_data(data):
    """ Constructs a new setting from a given dataset. This method will automatically
    instantiate a new class matching the type of the given dataset. It will fill
    all values provided by the dataset and then return the created instance """
    factory = {
        "color": ColorType,
        "scalar": ScalarType
    }
    if data["type"] not in factory:
        raise Exception("Unkown setting type: {}".format(data["type"]))
    instance = factory[data["type"]](data)
    if data:
        raise Exception("Unparsed data left in plugin setting: {}".format(data))
    return instance


class BaseType(RPObject):
    """ Base setting type for all setting types """
    glsl_type = None
    pta_type = None

    def __init__(self, data):
        self.type = data.pop("type")
        self.label = data.pop("label").strip()
        self.description = data.pop("description").strip()
        self.curves = []

        RPObject.__init__(self, "dsetting:{}".format(self.label))

    def get_value_at(self, offset):
        """ Returns the unscaled value at the given day time offset """
        return (curve.get_value(offset) for curve in self.curves)

    def get_scaled_value(self, value):
        """ Returns the scaled value from a given normalized value """
        raise NotImplementedError()

class ScalarType(BaseType):
    """ Setting type storing a single scalar """

    glsl_type = "float"
    pta_type = PTAFloat

    def __init__(self, data):
        self.unit = yaml.pop("unit")
        self.minvalue, self.maxvalue = yaml.pop("range")
        self.default = yaml.pop("default")

        if self.unit not in ("degree", "meter", "percent"):
            raise Exception("Invalid unit type: {}".format(self.unit))

    def format(self, value):
        """ Formats a given value, attaching the appropriate metric unit """
        metric = {
            "degree": u'\N{DEGREE SIGN}',
            "percent": u'%',
            "meter": u'm'
        }[self.unit]
        return "{:3.0f}{}".format(self.value, metric)

    def get_scaled_value(self, value):
        return value * (self.maxvalue - self.minvalue) + self.minvalue

    def get_linear_value(self, scaled_value):
        return (scaled_value - self.minvalue) / (self.maxvalue - self.minvalue)

class ColorType(BaseType):
    """ Setting type storing a RGB color triple """

    glsl_type = "vec3"
    pta_type = PTALVecBase3f

    def __init__(self):
        pass

    def format(self, value):
        return "{:3}, {:3}, {:3}".format(*value)

    def get_scaled_value(self, value):
        return (i * 255 for i in value)

    def get_linear_value(self, scaled_value):
        return (i / 255 for i in scaled_value)

