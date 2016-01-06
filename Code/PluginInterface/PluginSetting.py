from six import iteritems

from ..Util.DebugObject import DebugObject
from .PluginExceptions import BadSettingException

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
        self.shader_runtime = False
        self.display_conditions = {}

    def is_dynamic(self):
        """ Returns whether the setting is dynamic """
        return self.runtime or self.shader_runtime

    def evaluate_display_conditions(self, settings):
        """ Checks whether the setting should be visible for a given set of
        settings """
        for setting_id, required_value in iteritems(self.display_conditions):
            if setting_id not in settings:
                self.warn("Unkown display dependency setting:", setting_id)
                return False
            if isinstance(required_value, list) or isinstance(required_value, tuple):
                if settings[setting_id].value not in required_value:
                    return False
            else:
                if settings[setting_id].value != required_value:
                    return False
        return True

    @classmethod
    def load_from_yaml(cls, yaml):
        """ Constructs a new base plugin from a given yaml string """

        # Check if all base properties are set
        for prop in ["label", "description", "type", "default"]:
            if prop not in yaml:
                raise BadSettingException("Missing key: " + prop)

        # Find the type of the setting
        typename = yaml.pop("type").strip().upper()
        classname = "PluginSetting" + typename

        # Check if there is a typehandler for that type
        if classname in globals():
            instance = globals()[classname]()
        else:
            raise BadSettingException("Unkown type: " + typename)

        # Read the settings which are equal for each type
        instance.default = yaml.pop("default")
        instance.type = typename
        instance.label = yaml.pop("label").strip()
        instance.description = yaml.pop("description").strip()

        instance._rename("PSetting['" + instance.label + "']")

        # Check if the setting is changeable at runtime
        if "runtime" in yaml:
            instance.runtime = True if yaml.pop("runtime") else False

        if "shader_runtime" in yaml:
            instance.shader_runtime = True if yaml.pop("shader_runtime") else False

        # Load type specific settings
        try:
            instance.load_additional_settings(yaml)
        except Exception as msg:
            raise BadSettingException("Failed to init type:", msg)

        # Set default value, using the set_value function to check if the
        # default is valid
        instance.set_value(instance.default)
        instance.default = instance.value

        # Check for a display condition
        if "display_if" in yaml:
            instance.display_conditions = yaml.pop("display_if")

        # Check if all settings got "consumed"
        if yaml:
            raise BadSettingException("Unrecognized settings-keys: ", yaml.keys())

        return instance


# Specialized Plugin Settings

class PluginSettingINT(BasePluginSetting):

    """ Setting which stores a single integer """

    def load_additional_settings(self, yaml):
        int_range = yaml.pop("range")
        self.min_value = int(int_range[0])
        self.max_value = int(int_range[1])

    def set_value(self, val):
        try:
            val = int(val)
        except ValueError as msg:
            raise BadSettingException(msg)
        if val < self.min_value or val > self.max_value:
            self.warn("Given value exceeds value range: " + str(val))
        self.value = max(self.min_value, min(self.max_value, val))

class PluginSettingFLOAT(BasePluginSetting):

    """ Settings which stores a single float """

    def load_additional_settings(self, yaml):
        flt_range = yaml.pop("range")
        self.min_value = float(flt_range[0])
        self.max_value = float(flt_range[1])

    def set_value(self, val):
        try:
            val = float(val)
        except ValueError as msg:
            raise BadSettingException(msg)

        if val < self.min_value or val > self.max_value:
            self.warn("Given value exceeds value range: " + str(val))
        self.value = max(self.min_value, min(self.max_value, val))

class PluginSettingBOOL(BasePluginSetting):

    """ Setting which stores a single bool """

    def load_additional_settings(self, yaml):
        pass

    def set_value(self, val):
        if not isinstance(val, int) and not isinstance(val, bool):
            raise BadSettingException("Unkown data value for bool: "  + str(val))
        self.value = True if val else False

class PluginSettingENUM(BasePluginSetting):

    """ Setting which stores an enumeration """

    def load_additional_settings(self, yaml):
        self.values = yaml.pop("values")
        if not isinstance(self.values, list) and not isinstance(self.values, tuple):
            raise BadSettingException("Value enumeration is not a list")

    def set_value(self, val):
        if val not in self.values:
            raise BadSettingException("Value not contained in enumeration: " + str(val))
        self.value = val



class PluginSettingIMAGE(BasePluginSetting):

    """ Setting which stores a path to an image """

    def load_additional_settings(self, yaml):
        pass

    def set_value(self, val):
        self.value = val
