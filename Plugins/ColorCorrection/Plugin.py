# Load the plugin api
from .. import *

from .ColorCorrectionStage import ColorCorrectionStage

class Plugin(BasePlugin):

    def __init__(self, pipeline):
        BasePlugin.__init__(self, pipeline)

    @PluginHook("on_stage_setup")
    def setup_stages(self):
        """ This method gets called when the pipeline setups the render
        stages. You should create your custom stages here """

        # Disable default display stage to use our own stage
        get_internal_stage_handle(FinalStage).disable_stage()

        self._stage = self.create_stage(ColorCorrectionStage)