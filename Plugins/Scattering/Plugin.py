
from .. import *

from .ScatteringStage import ScatteringStage
from .ScatteringMethods import ScatteringMethodEricBruneton, ScatteringMethodHosekWilkie

# Create the main plugin
class Plugin(BasePlugin):

    def __init__(self, pipeline):
        BasePlugin.__init__(self, pipeline)

        self._method = ScatteringMethodEricBruneton(self)

    @PluginHook("on_pipeline_created")
    def on_create(self):
        self._method.load()
        self._method.compute()

    @PluginHook("on_stage_setup")
    def on_setup(self):
        self.debug("Setting up scattering stage ..")
        self._display_stage = self.create_stage(ScatteringStage)

    @PluginHook("on_shader_reload")
    def on_shader_reload(self):
        self._method.compute()
