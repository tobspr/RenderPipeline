
# Load plugin api
from .. import *

# Load some plugin classes here
from .SSLRStage import SSLRStage

# Create the main plugin
class Plugin(BasePlugin):

    @PluginHook("on_stage_setup")
    def setup_stages(self):
        self.debug("Setting up SSLR stage ..")
        self._sslr_stage = self.create_stage(SSLRStage)
