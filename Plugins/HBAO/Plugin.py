
# Load the plugin api
from .. import *

from .HBAOStage import HBAOStage

class Plugin(BasePlugin):

    def __init__(self, pipeline):
        BasePlugin.__init__(self, pipeline)

    @PluginHook("on_stage_setup")
    def setup_stages(self):
        self._hbao_stage = self.create_stage(HBAOStage)

        # Make the ambient stage use our output
        get_internal_stage_handle(AmbientStage).add_pipe_requirement("AmbientOcclusion")


    @PluginHook("on_pipeline_created")
    def init(self):
        pass

    @SettingChanged("some_setting")
    def update_some_setting(self):
        pass

