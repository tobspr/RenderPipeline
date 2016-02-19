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

from rpcore.rp_object import RPObject
from rpcore.util.smooth_connected_curve import SmoothConnectedCurve

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

    def __init__(self, data):
        self.type = data.pop("type")
        self.label = data.pop("label").strip()
        self.description = data.pop("description").strip()
        self.curves = []

        RPObject.__init__(self, "dsetting:{}".format(self.label))

    def get_value_at(self, offset):
        """ Returns the unscaled value at the given day time offset """
        if len(self.curves) == 1:
            return self.curves[0].get_value(offset)
        return tuple(curve.get_value(offset) for curve in self.curves)

    def get_scaled_value_at(self, offset):
        """ Returns the scaled value at a given day time offset """
        return self.get_scaled_value(self.get_value_at(offset))

    def get_scaled_value(self, value):
        """ Returns the scaled value from a given normalized value """
        raise NotImplementedError()

    def set_control_points(self, control_points):
        """ Sets the control points on the curves. """
        for curve_index, points in enumerate(control_points):
            self.curves[curve_index].control_points = points

class ScalarType(BaseType):
    """ Setting type storing a single scalar """

    glsl_type = "float"
    pta_type = PTAFloat

    def __init__(self, data):
        BaseType.__init__(self, data)
        self.unit = data.pop("unit")
        self.minvalue, self.maxvalue = data.pop("range")
        self.default = self.get_linear_value(data.pop("default"))

        if self.unit not in ("degree", "meter", "percent"):
            raise Exception("Invalid unit type: {}".format(self.unit))

        self.logarithmic_factor = data.pop("logarithmic_factor", 1.0) # TODO

        self.curves.append(SmoothConnectedCurve())
        self.curves[0].set_single_value(self.default)

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

    def __init__(self, data):
        BaseType.__init__(self, data)
        self.default = self.get_linear_value(data.pop("default"))
        colors = ((255, 0, 0), (0, 255, 0), (0, 0, 255))
        for i in range(3):
            curve = SmoothConnectedCurve()
            curve.set_single_value(self.default[i])
            curve.color = colors[i]
            self.curves.append(curve)

    def format(self, value):
        return "{:3}, {:3}, {:3}".format(*value)

    def get_scaled_value(self, value):
        return tuple(i * 255.0 for i in value)

    def get_linear_value(self, scaled_value):
        return tuple(i / 255.0 for i in scaled_value)
