
import collections

from direct.stdpy.file import open

from ..Util.DebugObject import DebugObject
from ..External.PyYAML import YAMLEasyLoad
from .PluginExceptions import BadSettingException
from .PluginSetting import BasePluginSetting

class PluginConfig(DebugObject):

    """ This class manages the loading of the plugin settings of each plugin.
    Each BasePlugin will have an instance of this class to load the plugin settings,
    in case a config file was found in the plugin directory """

    def __init__(self):
        DebugObject.__init__(self)
        self._properties = {}
        self._settings = collections.OrderedDict()
        self._loaded = False

    def get_name(self):
        """ Returns the name of the plugin """
        assert(self._loaded)
        return self._properties["name"]

    def get_description(self):
        """ Returns the description of the plugin """
        assert(self._loaded)
        return self._properties["description"]

    def get_version(self):
        """ Returns the version of the plugin """
        assert(self._loaded)
        return self._properties["version"]

    def get_author(self):
        """ Returns the author of the plugin """
        assert(self._loaded)
        return self._properties["author"]

    def get_settings(self):
        """ Returns a dictionary with all setting handles """
        return self._settings

    def get_setting(self, setting):
        """ Returns a setting by name, shortcut for get_setting_handle(name).value """
        return self.get_setting_handle(setting).value

    def get_setting_handle(self, setting):
        """ Returns a setting handle by name """
        assert(self._loaded)
        if setting not in self._settings:
            self.error("Could not find setting:", setting)
            return False
        return self._settings[setting]

    def consume_overrides(self, plugin_id, overrides):
        """ Given a list of overrides, apply those to the settings given by 
        this plugin. The overrides should be a dictionary, where the key
        is PluginID.setting_name, and the value is the new value. Settings from
        other plugins are ignored, unkown settings trigger an error. All matched
        settings will be removed from the dictionary. """
        assert(self._loaded)


        # need a copy to iterate
        for key in list(overrides.keys()):
            if key.startswith(plugin_id):
                setting_name = ".".join(key.split(".")[1:])
                setting_value = overrides[key]


                if setting_name not in self._settings:
                    self.warn("Unrecognized override: " + key)
                    del overrides[key]
                    continue
                    
                self._settings[setting_name].set_value(setting_value)

    def load(self, filename):
        """ Loads the plugin configuration from a given filename """

        parsed_yaml = YAMLEasyLoad(filename)

        # Make sure all required properties are set
        for prop in ["name", "author", "version", "description", "settings", "daytime_settings"]:
            if prop not in parsed_yaml:
                self.error("Missing key in plugin config:", prop)
                return False

        # Take out the settings, we process them seperately
        settings = parsed_yaml.pop("settings")

        # Strip line breaks and spaces from all string properties
        for key, value in parsed_yaml.items():
            if hasattr(value, "strip"):
                parsed_yaml[key] = value.strip("\r\n\t ")

        # Copy over the regular properties
        self._properties = parsed_yaml

        # Make the version a string
        self._properties["version"] = str(self._properties["version"])

        # Process the settings
        self._process_settings(settings)
        self._loaded = True

    def _process_settings(self, settings):
        """ Internal method to process the settings """

        # In case no setting are specified, the settings are not a dict, but
        # simply None, in that case just do nothing
        if settings is None:
            return

        if not isinstance(settings, list) or not isinstance(settings[0], tuple):
            self.error("Settings array is not an ordered map! (Declare it as !!omap).")
            return

        for setting_id, setting_value in settings:
            try:
                setting = BasePluginSetting.load_from_yaml(setting_value)
            except BadSettingException as msg:
                self.error("Could not parse setting", setting_id, msg)
                continue
            self._settings[setting_id] = setting

