
# Load plugin api
from .. import *

# Load some plugin classes here

# Create the main plugin
class Plugin(BasePlugin):

    NAME = "SMAA"
    DESCRIPTION = """ This plugin adds support for SMAA T2 """
    SETTINGS = {}

    def __init__(self, pipeline):
        BasePlugin.__init__(self, pipeline)



    @PluginHook("on_pipeline_create")
    def init(self):
        self._load_textures()

    def _load_textures(self):
        pass

