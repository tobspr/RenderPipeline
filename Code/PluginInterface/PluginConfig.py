
from direct.stdpy.file import open


from ..Util.DebugObject import DebugObject
from ..External.PyYAML import YAMLEasyLoad
from .PluginSetting import BasePluginSetting, BadSettingException

class PluginConfig(DebugObject):

    """ This class manages the loading of the plugin settings of each plugin.
    Each BasePlugin will have an instance of this class to load the plugin settings,
    in case a config file was found in the plugin directory """

    def __init__(self):
        DebugObject.__init__(self)
        self._properties = {}
        self._settings = {}
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

    def apply_overrides(self, overrides):
        """ Given a list of overrides, apply those to the settings given by 
        this plugin. The overrides should be a dictionary, where the key
        is PluginID.setting_name, and the value is the new value. Settings from
        other plugins are ignored, unkown settings trigger an error. """
        assert(self._loaded)
        self.debug("Applying overrides")

    def load(self, filename):
        """ Loads the plugin configuration from a given filename """

        parsed_yaml = YAMLEasyLoad(filename)

        # Make sure all required properties are set
        for prop in ["name", "author", "version", "description", "settings"]:
            if prop not in parsed_yaml:
                self.error("Missing key in plugin config:", prop)
                return False

        # Take out the settings, we process them seperately
        settings = parsed_yaml["settings"]
        del parsed_yaml["settings"]

        # Strip line breaks and spaces from all string properties
        for key, value in parsed_yaml.items():
            if hasattr(value, "strip"):
                parsed_yaml[key] = value.strip("\r\n\t ")

        # Copy over the regular properties
        self._properties = parsed_yaml

        # Process the settings
        self._process_settings(settings)
        self._loaded = True

    def _process_settings(self, settings):
        """ Internal method to process the settings """

        # In case no setting are specified, the settings are not a dict, but
        # simply None, in that case just do nothing
        if settings is None:
            return

        for setting_id in settings:
            try:
                setting = BasePluginSetting.load_from_yaml(settings[setting_id])
            except BadSettingException as msg:
                self.error("Could not parse setting", setting_id, msg)
                continue
            self._settings[setting_id] = setting

