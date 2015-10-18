
# Load plugin api
from .. import *

# Load some plugin classes here
from SSLRStage import SSLRStage

# Create the main plugin
class Plugin(BasePlugin):

    NAME = "PluginPrefab"
    DESCRIPTION = """ This plugin adds support for Screen Space Local Reflections """
    SETTINGS = {
    }

    def __init__(self, pipeline):
        BasePlugin.__init__(self, pipeline)

    @PluginHook("on_stage_setup")
    def create_stages(self):
        self.debug("Setting up stages")
        self._sslr_stage = SSLRStage(self._pipeline)
        self._pipeline.get_stage_mgr().add_stage(self._sslr_stage)
        


