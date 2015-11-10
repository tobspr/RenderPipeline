

from ..Util.DebugObject import DebugObject
from ..Util.Generic import consume

class BadSettingException(Exception):
    pass


class BasePluginSetting(DebugObject):
    
    """ This is the base plugin setting, which is used by the plugin config.
    It loads the basic properties from a YAML object """

    def __init__(self):
        DebugObject.__init__(self)
        self.value = None
        self.default = None
        self.type = None
        self.label = None
        self.description = None
        self.runtime = False

    @classmethod
    def load_from_yaml(cls, yaml):
        """ Constructs a new base plugin from a given yaml string """

        # Check if all base properties are set
        for prop in ["label", "description", "type", "default"]:
            if prop not in yaml:
                raise BadSettingException("Missing key: " + prop)

        # Find the type of the setting
        typename = consume(yaml, "type").strip().upper()
        classname = "PluginSetting" + typename

        # Check if there is a typehandler for that type
        if classname in globals():  
            instance = globals()[classname]()
        else:
            raise BadSettingException("Unkown type: " + typename)

        # Read the settings which are equal for each type
        instance.default = consume(yaml, "default")
        instance.type = typename
        instance.label = consume(yaml, "label").strip()
        instance.description = consume(yaml, "description").strip()

        # Check if the setting is changeable at runtime
        if "runtime" in yaml:
            instance.runtime = True if consume(yaml, "runtime") else False

        # Load type specific settings
        try:
            instance.load_additional_settings(yaml)
        except Exception as msg:
            raise BadSettingException("Failed to init type:", msg)
            
        # Finally set the value to the default
        instance.value = instance.default
        return instance


# Specialized Plugin Settings

class PluginSettingINT(BasePluginSetting):
    
    """ Setting which stores a single integer """

    def load_additional_settings(self, yaml):
        int_range = consume(yaml, "range")
        self.min_value = int(int_range[0])
        self.max_value = int(int_range[1])
        self.default = int(self.default)

        if self.default < self.min_value or self.default > self.max_value:
            raise BadSettingException("Default exceeds value range")

class PluginSettingFLOAT(BasePluginSetting):

    """ Settings which stores a single float """

    def load_additional_settings(self, yaml):
        flt_range = consume(yaml, "range")
        self.min_value = float(flt_range[0])
        self.max_value = float(flt_range[1])
        self.default = float(self.default)

        if self.default < self.min_value or self.default > self.max_value:
            raise BadSettingException("Default exceeds value range")

class PluginSettingBOOL(BasePluginSetting):
        
    """ Setting which stores a single bool """

    def load_additional_settings(self, yaml):
        self.default = True if self.default else False

class PluginSettingENUM(BasePluginSetting):

    """ Setting which stores an enumeration """

    def load_additional_settings(self, yaml):
        values = consume(yaml, "values")
        if not isinstance(values, list) and not isinstance(values, tuple):
            raise BadSettingException("Value enumeration is not a list")

        if self.default not in values:
            raise BadSettingException("Default value not contained in enumeration")


