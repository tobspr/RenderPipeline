
from os.path import join
import importlib

from direct.stdpy.file import open, isfile

from ..Util.DebugObject import DebugObject
from ..External.PyYAML import YAMLEasyLoad
from .PluginInterface import PluginInterface

class PluginManager(DebugObject):

    """ This class manages the loading and handling of plugins. It uses the
    PluginInterface internally to read the configuration. """

    def __init__(self, pipeline):
        DebugObject.__init__(self)
        self._pipeline = pipeline
        self._interface = PluginInterface()
        self._plugin_instances = []
        self._hooks = {}

        # Load enabled plugin list
        self._interface.set_base_dir(".")
        self._interface.load_plugin_config()

    def load_plugins(self):
        """ Loads all plugins from the plugin directory """
        self.debug("Loading plugins ..")
        failed_plugins = []

        # Try to load all enabled plugins
        for plugin in self._interface.get_enabled_plugins():
            plugin_class = self._try_load_plugin(plugin)

            if plugin_class:
                # In case the plugin loaded, create a instance of it, register
                # the settings and initializes it.
                plugin_instance = plugin_class(self._pipeline)
                plugin_instance.get_config().consume_overrides(plugin,
                    self._interface.get_overrides())
                self._plugin_instances.append(plugin_instance)
                self.debug("Loaded", plugin_instance.get_config().get_name())
            else:
                failed_plugins.append(plugin)

        # Unregister plugins which failed to load
        for plugin in failed_plugins:
            self._interface.disable_plugin(plugin)

    def reload_settings(self):
        """ Reloads all plugin settings from the plugin config file """
        self.debug("Reloading plugin settings ...")
        self._interface.load_plugin_config()

        for plugin in self._plugin_instances:
            plugin.get_config().consume_overrides(plugin.get_id(),
                self._interface.get_overrides())

    def on_setting_change(self, setting_name):
        """ This method gets called when a setting got dynamically changed """
        self.reload_settings()

        setting_name = setting_name.split(".")
        if len(setting_name) != 2:
            return

        plugin_id = setting_name[0]
        setting_id = setting_name[1]

        # Find the certain plugin
        for plugin in self._plugin_instances:
            if plugin.get_id() == plugin_id:
                handle = plugin.get_config().get_setting_handle(setting_id)

                # Check if the setting is actually dynamic (should always be)
                if not handle.is_dynamic():
                    self.warn("Got dynamic update, but setting is not dynamic:", setting_id)
                    return

                # Trigger eventually assigned hooks
                plugin.handle_setting_change(setting_id)

                # Reload shaders if necessarry
                if handle.shader_runtime:

                    # Define new plugin settings
                    plugin.define_static_plugin_settings()

                    # Make sure the updated settings are written
                    self._pipeline.get_stage_mgr().write_autoconfig()

                    # Update only the plugin shaders
                    plugin.reload_stage_shaders()

                    # Trigger an explicit reload hook
                    plugin.trigger_hook_explicit("on_shader_reload")


    def _try_load_plugin(self, plugin_id):
        """ Attempts to load a plugin with a given name """
        plugin_path = join("Plugins", plugin_id)
        plugin_main = join(plugin_path, "__init__.py")
        if not isfile(plugin_main):
            self.warn("Cannot load",plugin_id,"because __init__.py was not found")
            return None

        module_path = "Plugins." + plugin_id + ".Plugin"

        try:
            module = importlib.import_module(module_path)
        except Exception as msg:
            self.warn("Could not import",plugin_id,"because of an import error:")
            self.warn(msg)
            return None
            
        if not hasattr(module, "Plugin"):
            self.warn("Plugin",plugin_id,"has no main Plugin class defined!")
            return None

        return module.Plugin

    def add_hook_binding(self, hook_name, handler):
        """ Attaches a new handler to a hook """
        if hook_name in self._hooks:
            self._hooks[hook_name].append(handler)
        else:
            self._hooks[hook_name] = [handler]

    def trigger_hook(self, hook_name):
        """ Triggers a hook, executing all handlers attached to that hook """
        if hook_name in self._hooks:
            for handler in self._hooks[hook_name]:
                handler()
                
    def init_defines(self):
        """ Creates the defines which can be used in shaders """
        self.debug("Initializing defines")
        for plugin in self._interface.get_enabled_plugins():
            self._pipeline.get_stage_mgr().define("HAVE_PLUGIN_" + plugin, 1)
            
        for instance in self._plugin_instances:
            instance.define_static_plugin_settings()


