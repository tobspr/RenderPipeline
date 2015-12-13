# Load the plugin api
from .. import *

from .BloomStage import BloomStage

class Plugin(BasePlugin):

    @PluginHook("on_stage_setup")
    def setup_stages(self):
        self._bloom_stage = self.create_stage(BloomStage)
        