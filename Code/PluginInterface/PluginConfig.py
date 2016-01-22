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
from six import iteritems

import collections

from ..Util.DebugObject import DebugObject
from ..External.PyYAML import YAMLEasyLoad
from .PluginExceptions import BadSettingException
from .PluginSetting import BasePluginSetting
from ..DayTime.DayTimeSetting import DayTimeSetting

class PluginConfig(DebugObject):

    """ This class manages the loading of the plugin settings of each plugin.
    Each BasePlugin will have an instance of this class to load the plugin settings,
    in case a config file was found in the plugin directory """

    def __init__(self):
        DebugObject.__init__(self)
        self._properties = {}
        self._settings = collections.OrderedDict()
        self._daytime_settings = collections.OrderedDict()
        self._loaded = False

    def get_name(self):
        """ Returns the name of the plugin """
        assert self._loaded
        return self._properties["name"]

    def get_description(self):
        """ Returns the description of the plugin """
        assert self._loaded
        return self._properties["description"]

    def get_version(self):
        """ Returns the version of the plugin """
        assert self._loaded
        return self._properties["version"]

    def get_author(self):
        """ Returns the author of the plugin """
        assert self._loaded
        return self._properties["author"]

    def get_settings(self):
        """ Returns a dictionary with all setting handles """
        assert self._loaded
        return self._settings

    def get_requires_native(self):
        """ Returns whether the plugin requires the native modules """
        return "requires_native" in self._properties and self._properties["requires_native"]

    def get_daytime_settings(self):
        """ Returns a dictionary with all daytime setting handles """
        assert self._loaded
        return self._daytime_settings

    def get_setting(self, setting):
        """ Returns a setting by name, shortcut for get_setting_handle(name).value """
        return self.get_setting_handle(setting).value

    def get_setting_handle(self, setting):
        """ Returns a setting handle by name """
        assert self._loaded
        if setting not in self._settings:
            self.error("Could not find setting:", setting)
            return None
        return self._settings[setting]

    def apply_overrides(self, plugin_id, overrides):
        """ Given a list of overrides, apply those to the settings given by
        this plugin. The overrides should be a dictionary, where the key
        is PluginID.setting_name, and the value is the new value. Settings from
        other plugins are ignored, unkown settings trigger an error """
        assert self._loaded

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

    def apply_daytime_curves(self, curves):
        """ Applies all daytime curves from the daytime configuration file
        to the current settings """

        for setting_id, curve in iteritems(curves):
            if setting_id not in self._daytime_settings:
                self.warn("Unrecognized daytime override: " + setting_id)
                continue
            self._daytime_settings[setting_id].set_cv_points(curve)

    def load(self, filename):
        """ Loads the plugin configuration from a given filename """

        parsed_yaml = YAMLEasyLoad(filename)

        # Make sure all required properties are set
        for prop in ["name", "author", "version", "description", "settings",
                     "daytime_settings"]:
            if prop not in parsed_yaml:
                self.error("Missing key in plugin config:", prop)
                return False

        # Take out the settings, we process them seperately
        settings = parsed_yaml.pop("settings")
        daytime_settings = parsed_yaml.pop("daytime_settings")

        # Strip line breaks and spaces from all string properties
        for key, value in iteritems(parsed_yaml):
            if hasattr(value, "strip"):
                parsed_yaml[key] = value.strip("\r\n\t ")

        # Copy over the regular properties
        self._properties = parsed_yaml

        # Make the version a string
        self._properties["version"] = str(self._properties["version"])

        # Process the settings
        self._process_settings(settings)
        self._process_daytime_settings(daytime_settings)
        self._loaded = True

    def _process_settings(self, settings):
        """ Internal method to process the settings """
        # In case no settings are specified, the settings are not a dict, but
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
                self.error("Could not parse setting", setting_id, "->", msg)
                continue
            self._settings[setting_id] = setting

    def _process_daytime_settings(self, settings):
        """ Internal method to process the daytime settings """
        # In case no settings are specified, the settings are not a dict, but
        # simply None, in that case just do nothing
        if settings is None:
            return

        if not isinstance(settings, list) or not isinstance(settings[0], tuple):
            self.error("Daytime-Settings array is not an ordered map! (Declare it as !!omap).")
            return

        for setting_id, setting_value in settings:
            try:
                setting = DayTimeSetting.load_from_yaml(setting_value)
            except BadSettingException as msg:
                self.error("Could not parse daytime setting", setting_id, ":", msg)
                continue
            self._daytime_settings[setting_id] = setting
