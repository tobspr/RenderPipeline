
from .Util.DebugObject import DebugObject

from .Stages.AmbientStage import AmbientStage
from .Stages.GBufferStage import GBufferStage
from .Stages.FinalStage import FinalStage
from .Stages.DownscaleZStage import DownscaleZStage

class CommonStages(DebugObject):

    """ Setups commonly used stages for the pipeline """

    def __init__(self, pipeline):
        """ Inits the common stages """
        DebugObject.__init__(self)
        self._pipeline = pipeline
        self._init_stages()

    def _init_stages(self):
        """ Performs the stage setup """

        add_stage = self._pipeline.get_stage_mgr().add_stage

        self._ambient_stage = AmbientStage(self._pipeline)
        add_stage(self._ambient_stage)

        self._gbuffer_stage = GBufferStage(self._pipeline)
        add_stage(self._gbuffer_stage)

        self._final_stage = FinalStage(self._pipeline)
        add_stage(self._final_stage)

        # self._downscale_z_stage = DownscaleZStage(self._pipeline)
        # self._pipeline.get_stage_mgr().add_stage(self._downscale_z_stage)
