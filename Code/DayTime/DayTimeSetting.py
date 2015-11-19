
from ..Util.DebugObject import DebugObject
from ..PluginInterface.PluginExceptions import BadSettingException

class DayTimeSetting(DebugObject):
    
    """ This is the base class for all daytime settings where each specialized
    daytime setting derives from """

    def __init__(self):
        DebugObject.__init__(self)
        self.type = None
        self.label = None
        self.description = None
        self.default = None
        self.cvs = []

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
        if self.unit not in ["degree", "percent"]:
            raise BadSettingException("Unkown unit: ", self.unit)

    def set_default_value(self, val):
        val = float(val)
        if val < self.min_value or val > self.max_value:
            raise BadSettingException("Default out of range:", val)
        self.default = float(val)

class DayTimeSettingCOLOR(DayTimeSetting):

    """ Setting which stores a color """

    def load_additional_settings(self, yaml):
        pass

    def set_default_value(self, val):
        if not isinstance(val, list) and not isinstance(val, tuple):
            raise BadSettingException("Defaults for colors should be a list")

        if len(val) != 3:
            raise BadSettingException("Invalid component count for color, should be 3 but is", len(val))

        self.default = val
