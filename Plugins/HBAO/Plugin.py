
# Load plugin api
from .. import *

# Load some plugin classes
from .HBAOStage import HBAOStage

# Create the main plugin
class Plugin(BasePlugin):

    def __init__(self, pipeline):
        BasePlugin.__init__(self, pipeline)

    @PluginHook("on_shader_create")
    def create_stages(self):
        pass

    @PluginHook("on_pipeline_created")
    def reload_shaders(self):
        pass

