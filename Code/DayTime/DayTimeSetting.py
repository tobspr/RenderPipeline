# -*- encoding: utf-8 -*-

from panda3d.core import PTAFloat, PTAVecBase3f

from ..Util.DebugObject import DebugObject
from ..PluginInterface.PluginExceptions import BadSettingException
from ..Util.SmoothConnectedCurve import SmoothConnectedCurve

class DayTimeSetting(DebugObject):
    
    """ This is the base class for all daytime settings where each specialized
    daytime setting derives from """

    def __init__(self):
        DebugObject.__init__(self)
        self.type = None
        self.label = None
        self.description = None
        self.default = None
        self.curves = []

    def was_modified(self):
        """ Returns wheter any of the curves were modified """
        for curve in self.curves:
            if curve.was_modified():
                return True
        return False
    
    def serialize(self):
        return ("[" + "{},"*len(self.curves) ).format(*[i.serialize() for i in self.curves]).rstrip(",") + "]"

    def set_cv_points(self, points):
        for i, point_data in enumerate(points):
            self.curves[i].set_cv_points(point_data)

    @classmethod
    def load_from_yaml(cls, yaml):
        """ Constructs a new daytime setting from a given yaml string """

        # Check if all base properties are set
        for prop in ["type", "label", "description", "default"]:
            if prop not in yaml:
                raise BadSettingException("Missing key: " + prop)

        # Get the setting type
        setting_type = yaml.pop("type").strip().upper()
        classname = "DayTimeSetting" + setting_type
            
        if classname in globals():
            instance = globals()[classname]()
        else:
            raise BadSettingException("Unkown type: " + setting_type)

        instance.type = setting_type
        instance.default = yaml.pop("default")
        instance.label = yaml.pop("label").strip()
        instance.description = yaml.pop("description").strip()

        try:
            instance.load_additional_settings(yaml)
            instance.init_curves()
        except Exception as msg:
            raise BadSettingException("Failed to init type:", msg)

        instance.set_default_value(instance.default)        

        if yaml:
            raise BadSettingException("Unrecognized settings-keys:", yaml.keys())

        return instance

class DayTimeSettingSCALAR(DayTimeSetting):

    """ Setting which stores a single scalar """

    def load_additional_settings(self, yaml):
        self.min_value, self.max_value = yaml.pop("range")
        self.unit = yaml.pop("unit")
        if self.unit not in ["degree", "percent", "meter"]:
            raise BadSettingException("Unkown unit: ", self.unit)

    def set_default_value(self, val):
        val = float(val)
        if val < self.min_value or val > self.max_value:
            raise BadSettingException("Default out of range:", val)
        self.default = float(val)

    def format(self, val):
        if self.unit is None:
            return val
        elif self.unit == "degree":
            return str(round(val, 1)) + u"°"
        elif self.unit == "percent":
            return str(round(val, 2)) + u"%" 
        elif self.unit == "meter":
            return str(int(val)) + u"m" 

    def format_nonlinear(self, val):
        return self.format(self.from_linear_space(val))

    def to_linear_space(self, val):
        return max(0, min(1, (float(val) - self.min_value) / (self.max_value - self.min_value)))

    def from_linear_space(self, val):
        return float(max(0, min(1, val))) * (self.max_value - self.min_value) + self.min_value

    def init_curves(self):
        curve = SmoothConnectedCurve()
        curve.set_single_value(self.to_linear_space(self.default))
        self.curves = [curve]

    def get_value(self, offset):
        return self.from_linear_space(self.curves[0].get_value(offset))

    def get_scaled_value(self, offset):
        return self.get_value(offset)

    def get_pta_type(self):
        return PTAFloat

    def get_glsl_type(self):
        return "float"


class DayTimeSettingCOLOR(DayTimeSetting):

    """ Setting which stores a color """

    def load_additional_settings(self, yaml):
        pass

    def set_default_value(self, val):
        if not isinstance(val, list) and not isinstance(val, tuple):
            raise BadSettingException("Defaults for colors should be a list")

        if len(val) != 3:
            raise BadSettingException("Invalid component count for color, should be 3 but is", len(val))

        for comp in val:
            if comp < 0 or comp > 255:
                raise BadSettingException("Color component out of range: " + comp)

        self.default = val

    def format(self, val):
        s = "[{:3.0f} {:3.0f} {:3.0f}]".format(*val)
        return s

    def format_nonlinear(self, val):
        if isinstance(val, list):
            return self.format(val)
        else:
            return str(round(val, 2))

    def init_curves(self):
        curve_r = SmoothConnectedCurve()
        curve_g = SmoothConnectedCurve()
        curve_b = SmoothConnectedCurve()

        curve_r.set_color(255, 0, 0)
        curve_g.set_color(0, 255, 0)
        curve_b.set_color(0, 0, 255)

        curve_r.set_single_value(self.default[0] / 255.0)
        curve_g.set_single_value(self.default[1] / 255.0)
        curve_b.set_single_value(self.default[2] / 255.0)

        self.curves = [curve_r, curve_g, curve_b]

    def get_value(self, offset):
        return (min(255, self.curves[0].get_value(offset) * 255.0),
                min(255, self.curves[1].get_value(offset) * 255.0),
                min(255, self.curves[2].get_value(offset) * 255.0))

    def get_scaled_value(self, offset):
        return (min(1.0, self.curves[0].get_value(offset)),
                min(1.0, self.curves[1].get_value(offset)),
                min(1.0, self.curves[2].get_value(offset)))

    def get_pta_type(self):
        return PTAVecBase3f

    def get_glsl_type(self):
        return "vec3"
