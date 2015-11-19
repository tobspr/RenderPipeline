
from ..Util.DebugObject import DebugObject
from .PluginInterface import PluginInterface

class PluginManager(DebugObject):

    """ This class manages the loading and handling of plugins. It uses the
    PluginInterface internally to manage plugins. """

    def __init__(self, pipeline):
        DebugObject.__init__(self)
        self._pipeline = pipeline
        self._hooks = {}

        # Construct plugin interface
        self._interface = PluginInterface(self._pipeline)
        self._interface.set_base_dir(".")
        self._interface.load_plugin_config()

    def reload_settings(self):
        """ Reloads all plugin settings from the plugin config file """
        self.debug("Reloading plugin settings ...")
        self._interface.load_plugin_config()
        self._interface.reload_overrides()

    def get_interface(self):
        """ Returns a handle to the plugin interface """
        return self._interface

    def load_plugins(self):
        """ Loads all enabled plugins """
        self._interface.load_plugins()

    def on_setting_change(self, setting_name):
        """ This method gets called when a setting got dynamically changed """
        self.reload_settings()

        setting_name = setting_name.split(".")
        if len(setting_name) != 2:
            return

        plugin_id, setting_id = setting_name
        plugin = self._interface.get_plugin_handle(plugin_id)

        # Get a handle to the setting and trigger eventually assigned hooks
        handle = plugin.get_config().get_setting_handle(setting_id)
        plugin.handle_setting_change(setting_id)

        # Reload shaders if necessarry
        if handle.shader_runtime:

            # Define new plugin settings and write it to the autoconfig
            plugin.define_static_plugin_settings()
            self._pipeline.get_stage_mgr().write_autoconfig()

            # Update the plugin shaders a,d trigger an expplicit reload hook
            plugin.reload_stage_shaders()
            plugin.trigger_hook_explicit("on_shader_reload")

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
        """ Creates various plugin defines which can be used in shaders """
        self.debug("Initializing defines ..")
        for plugin in self._interface.get_enabled_plugins():
            self._pipeline.get_stage_mgr().define("HAVE_PLUGIN_" + plugin, 1)
            
        for instance in self._interface.get_plugin_instances():
            instance.define_static_plugin_settings()
