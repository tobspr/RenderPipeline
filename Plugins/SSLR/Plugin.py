
# Load plugin api
from .. import *

# Load some plugin classes here
from .SSLRStage import SSLRStage

# Create the main plugin
class Plugin(BasePlugin):

    def __init__(self, pipeline):
        BasePlugin.__init__(self, pipeline)

    @PluginHook("on_stage_setup")
    def create_stages(self):
        self.debug("Setting up SSLR stage ..")
        self._sslr_stage = self.make_stage(SSLRStage)
        self.register_stage(self._sslr_stage)
