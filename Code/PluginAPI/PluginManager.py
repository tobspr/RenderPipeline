
import re

from direct.stdpy.file import open, isfile
from Plugin import Plugin

from ..Util.DebugObject import DebugObject


class PluginManager(DebugObject):

    """ This class manages the loading and handling of plugins """

    def __init__(self, pipeline):
        DebugObject.__init__(self)
        self._pipeline = pipeline
        self._valid_name_regexp = re.compile('^[a-zA-Z0-9_]+$')
        self._plugin_instances = []

    def load_plugins(self):
        """ Loads all plugins from the plugin directory """
        plugins = self._load_plugin_config()

        for plugin in plugins:
            self.debug("Loading plugin", plugin)
            plugin_class = self._try_load_plugin(plugin)
            self._plugin_instances.append(plugin_class(self._pipeline))

    def _load_plugin_config(self):
        """ Loads the plugin config and extracts the list of activated plugins """
        plugin_cfg = "Config/plugins.ini"
        self.debug("Loading plugin config")
        if not isfile(plugin_cfg):
            self.error("Could not open '" + plugin_cfg + "'")

        with open(plugin_cfg, "r") as handle:
            lines = handle.readlines()

        activated_plugins = set()
        for line in lines:
            if line.startswith("require="):
                plugin_name = line.split("=")[-1].strip('";\n')
                # Make sure the plugin name is valid
                if not self._valid_name_regexp.match(plugin_name):
                    self.warn("Invalid plugin name: '" + plugin_name + "'")
                    continue
                activated_plugins.add(plugin_name)

        return activated_plugins

    def _try_load_plugin(self, plugin_id):
        """ Attempts to load a plugin with a given name """
        plugin_path = "Plugins/" + plugin_id + "/"
        plugin_main = plugin_path + "__init__.py"
        if not isfile(plugin_main):
            self.warn("Cannot load",plugin_id,"because __init__.py was not found")
            return

        # I tried everything, but imp and importlib don't seem to import the 
        # module in the current package. Until I haven't found a better solution,
        # I have to use this ugly code.
        imp_str = "from ...Plugins.{0}.Plugin{0} import Plugin{0} as TempPlugin"
        exec(imp_str.format(plugin_id))
        return TempPlugin

    def trigger_hook(self, hook_name):
        """ Triggers the hook, executing all handlers attached to that hook """
        pass
