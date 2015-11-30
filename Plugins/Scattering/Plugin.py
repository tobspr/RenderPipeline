
from .. import *

from .ScatteringStage import ScatteringStage

# Create the main plugin
class Plugin(BasePlugin):

    @PluginHook("on_pipeline_created")
    def on_create(self):
        self._method.load()
        self._method.compute()

    @PluginHook("on_stage_setup")
    def on_setup(self):
        self.debug("Setting up scattering stage ..")
        self._display_stage = self.create_stage(ScatteringStage)

        # Load scattering method
        method = self.get_setting("scattering_method")

        self.debug("Loading scattering method for '" + method + "'")

        if method == "eric_bruneton":
            from .ScatteringMethods import ScatteringMethodEricBruneton
            self._method = ScatteringMethodEricBruneton(self)
        elif method == "hosek_wilkie":
            from .ScatteringMethods import ScatteringMethodHosekWilkie
            self._method = ScatteringMethodHosekWilkie(self)
        else:
            self.error("Unrecognized scattering method!")

    @PluginHook("on_shader_reload")
    def on_shader_reload(self):
        self._method.compute()
