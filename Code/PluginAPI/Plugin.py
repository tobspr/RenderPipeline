

from ..Util.DebugObject import DebugObject

class Plugin(DebugObject):

    """ This is the base plugin class from which all plugins should derive. """

    def __init__(self, pipeline, plugin_name = "default"):
        """ Constructs the plugin, also checks is all plugin properties are set
        properly """
        DebugObject.__init__(self, "Plugin::" + plugin_name)
        self._pipeline = pipeline

        # Set a special output color for plugins
        self._set_debug_color("magenta", "bright")

        if not hasattr(self, "NAME"):
            self.warn("No plugin name defined!")
        if not hasattr(self, "DESCRIPTION"):
            self.warn("No plugin description defined!")
        if not hasattr(self, "SETTINGS"):
            self.warn("No plugin settings defined!")

    def _bind_to_hook(self, hook_name, handler):
        """ Binds the handler to a given hook_name. When the hook is executed
        in the pipeline code, the handler gets called """
        self.debug("Binding to hook", hook_name)

