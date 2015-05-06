

from DebugObject import DebugObject

class AmbientOcclusionManager(DebugObject):

    def __init__(self, pipeline):
        DebugObject.__init__(self, "AmbientOcclusion")
        self.pipeline = pipeline
        self.create()

    def create(self):
        self.debug("Creating occlusion pass")

        technique = self.pipeline.settings.occlusionTechnique

        print technique