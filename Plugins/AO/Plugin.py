
# Load the plugin api
from .. import *

from .AOStage import AOStage

class Plugin(BasePlugin):

    @PluginHook("on_stage_setup")
    def setup_stages(self):
        self._stage = self.create_stage(AOStage)

        # Make the ambient stage use our output
        get_internal_stage("AmbientStage").add_pipe_requirement("AmbientOcclusion")
        get_internal_stage("ApplyLightsStage").add_pipe_requirement("AmbientOcclusion")
