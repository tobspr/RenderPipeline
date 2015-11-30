
# Load the plugin api
from .. import *

from .AOStage import AOStage

class Plugin(BasePlugin):

    @PluginHook("on_stage_setup")
    def setup_stages(self):
        self._stage = self.create_stage(AOStage)

        # Make the ambient stage use our output
        get_internal_stage_handle(AmbientStage).add_pipe_requirement("AmbientOcclusion")
        get_internal_stage_handle(ApplyLightsStage).add_pipe_requirement("AmbientOcclusion")

    @PluginHook("on_pipeline_created")
    def init(self):
        pass

    @SettingChanged("some_setting")
    def update_some_setting(self):
        pass

