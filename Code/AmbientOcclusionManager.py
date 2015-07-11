

from DebugObject import DebugObject

from .RenderPasses.AmbientOcclusionPass import AmbientOcclusionPass
from .RenderPasses.OcclusionBlurPass import OcclusionBlurPass

class AmbientOcclusionManager(DebugObject):

    """ The ambient occlusion manager handles the setup of the passes required
    to compute ambient occlusion. He also registers the configuration defines
    specified in the pipeline configuration """

    availableTechniques = ["SAO", "HBAO", "TSAO", "None"]

    def __init__(self, pipeline):
        """ Creates the manager and directly creates the passes """
        DebugObject.__init__(self, "AmbientOcclusion")
        self.pipeline = pipeline
        self.create()

    def create(self):
        """ Creates the passes required to compute the occlusion, selecting
        the appropriate pass for the selected technique """

        technique = self.pipeline.settings.occlusionTechnique

        if technique not in self.availableTechniques:
            self.error("Unrecognized technique: " + technique)
            return

        if technique == "None":
            return

        # Create the ambient occlusion pass. The technique is selected in the 
        # shader later, based on the defines
        self.aoPass = AmbientOcclusionPass()
        self.pipeline.getRenderPassManager().registerPass(self.aoPass)

        # Create the ambient occlusion blur pass
        self.blurPass = OcclusionBlurPass()
        self.pipeline.getRenderPassManager().registerPass(self.blurPass)

        # Register the configuration defines
        self.pipeline.getRenderPassManager().registerDefine("OCCLUSION_TECHNIQUE_" + technique, 1)
        self.pipeline.getRenderPassManager().registerDefine("USE_OCCLUSION", 1)
        self.pipeline.getRenderPassManager().registerDefine("OCCLUSION_RADIUS", 
            self.pipeline.settings.occlusionRadius)
        self.pipeline.getRenderPassManager().registerDefine("OCCLUSION_STRENGTH", 
            self.pipeline.settings.occlusionStrength)
        self.pipeline.getRenderPassManager().registerDefine("OCCLUSION_SAMPLES", 
            self.pipeline.settings.occlusionSampleCount)
        if self.pipeline.settings.useTemporalOcclusion:
            self.pipeline.getRenderPassManager().registerDefine("ENHANCE_TEMPORAL_OCCLUSION", 1)
