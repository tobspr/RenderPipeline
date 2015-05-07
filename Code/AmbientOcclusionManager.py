

from DebugObject import DebugObject

from Code.RenderPasses.AmbientOcclusionPass import AmbientOcclusionPass

class AmbientOcclusionManager(DebugObject):

    availableTechniques = ["SAO", "HBAO", "NONE"]

    def __init__(self, pipeline):
        DebugObject.__init__(self, "AmbientOcclusion")
        self.pipeline = pipeline
        self.create()

    def create(self):
        self.debug("Creating occlusion pass")

        technique = self.pipeline.settings.occlusionTechnique

        if technique not in self.availableTechniques:
            self.error("Unrecognized ambient occlusion technique: " + technique)
            return

        if technique == "NONE":
            return

        self.aoPass = AmbientOcclusionPass()
        self.pipeline.getRenderPassManager().registerPass(self.aoPass)

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
