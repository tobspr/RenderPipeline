

import collections

from direct.stdpy.file import listdir, join, isfile

from ..Util.DebugObject import DebugObject
from ..PluginInterface.Virtual.VirtualPluginInterface import VirtualPluginInterface
from ..External.PyYAML import YAMLEasyLoad

class DayTimeManager(DebugObject):

    """ This class manages the time of day. It stores and controls the settings
    which change over the time of day, and also handles loading and saving
    of them """

    def __init__(self, interface):
        """ Constructs a new DayTime, the interface should be a handle to a 
        BasePluginInterface or any derived class of that """
        DebugObject.__init__(self)
        self._interface = interface
        self._base_dir = "."

    def set_base_dir(self, directory):
        """ Sets the base directory of the pipeline, in case its not the current
        working directory """
        self._base_dir = directory

    def load(self):
        """ Loads all daytime settings and overrides """
        # The plugin config does the actual work of loading the settings.
        # We just have to take care of the overrides:
        self._load_overrides()

    def _load_overrides(self):
        """ Loads the overrides from the daytime config file """
        plugin_file = join(self._base_dir, "Config/daytime.yaml")

        if not isfile(plugin_file):
            self.error("Could not load daytime overrides, file not found: ", plugin_file)
            return False

        yaml = YAMLEasyLoad(plugin_file)

        if "control_points" not in yaml:
            self.error("Root entry 'control_points' not found in daytime settings!")
            return False

        control_points = yaml["control_points"]
        
        # When there are no points, the object will be just none instead of an
        # empty dict
        if control_points is None:
            return

        available_plugins = self._interface.get_available_plugins()

        for plugin_id, cvs in control_points.items():

            # Skip invalid plugin ids
            if plugin_id not in available_plugins:
                self.warn("Skipping invalid plugin with id", plugin_id)
                continue

            plugin_handle = self._interface.get_plugin_handle(plugin_id)
            if not plugin_handle:
                self.warn("Could not get plugin handle for", plugin_id)
                continue

            plugin_handle.get_config().apply_daytime_curves(cvs)
