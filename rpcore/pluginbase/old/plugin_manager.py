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

from ..rp_object import RPObject
from .plugin_interface import PluginInterface
from .plugin_exceptions import PluginConfigError

class PluginManager(RPObject):

    """ This class manages the loading and handling of plugins. It uses the
    PluginInterface internally to manage plugins. """

    def __init__(self, pipeline):
        RPObject.__init__(self)
        self._pipeline = pipeline
        self._hooks = {}

        # Construct plugin interface
        self._interface = PluginInterface(self._pipeline)
        self._interface.load_plugin_config()

    def reload_settings(self):
        """ Reloads all plugin settings from the plugin config file """
        self.debug("Reloading plugin settings ...")
        try:
            self._interface.load_plugin_config()
        except PluginConfigError as msg:
            self.error("Failed to reload config:", msg)
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
            self.warn("Invalid setting change:", setting_name)
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
            self._pipeline.stage_mgr.write_autoconfig()

            # Update the plugin shaders a,d trigger an expplicit reload hook
            plugin.reload_stage_shaders()
            plugin.trigger_hook_explicit("on_shader_reload")

    def add_hook_binding(self, hook_name, handler):
        """ Attaches a new handler to a hook """
        if hook_name in self._hooks:
            self._hooks[hook_name].append(handler)
        else:
            self._hooks[hook_name] = [handler]

    def remove_hook_binding(self, hook_name, handler):
        """ Removes a handler from a hook """
        if hook_name not in self._hooks:
            self.error("Attempted to remove hook handler from", hook_name, "but hook is not present!")
            return
        self._hooks[hook_name].remove(handler)

    def trigger_hook(self, hook_name):
        """ Triggers a hook, executing all handlers attached to that hook """
        if hook_name in self._hooks:
            for handler in self._hooks[hook_name]:
                handler()

    def init_defines(self):
        """ Creates various plugin defines which can be used in shaders """
        self.debug("Initializing defines ..")
        for plugin in self._interface.get_enabled_plugins():
            self._pipeline.stage_mgr.define("HAVE_PLUGIN_" + plugin, 1)

        for instance in self._interface.get_plugin_instances():
            instance.define_static_plugin_settings()

    def reset_plugin_settings(self, plugin_id):
        """ Resets all settings of a given plugin """
        pass

    def save_overrides(self, override_file):
        """ Saves all overrides to a given override file """

