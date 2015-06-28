

from panda3d.core import PTAVecBase2f, Vec2

from DebugObject import DebugObject
from Globals import Globals

from .RenderPasses.AntialiasingFXAAPass import AntialiasingFXAAPass
from .RenderPasses.AntialiasingSMAAPass import AntialiasingSMAAPass

class AntialiasingManager(DebugObject):

    """ The Antialiasing Manager handles the setup of the antialiasing passes, 
    if antialiasing is defined in the settings. It also handles jittering when
    using a temporal antialiasing technique like SMAA.

    When jittering is enabled, the frame is moved by half a pixel up/down every 
    second frame, and then merged with the previous frame result, to achieve 
    better antialiasing. This is like MSAA but splitted over several frames """

    availableTechniques = ["FXAA", "SMAA", "None"]

    def __init__(self, pipeline):
        """ Creates the manager and directly setups the passes """
        DebugObject.__init__(self, "AntialiasingManager")
        self.pipeline = pipeline
        self.jitter = False
        self.jitterOffsets = []
        self.jitterIndex = 0
        self.jitterPTA = PTAVecBase2f.emptyArray(1)
        self.create()

    def create(self):
        """ Setups the antialiasing passes, and also computes the jitter offsets """

        technique = self.pipeline.settings.antialiasingTechnique

        if technique not in self.availableTechniques:
            self.error("Unrecognized antialiasing technique: " + technique)
            return

        # No antialiasing
        elif technique == "None":
            return

        # FXAA 3.11 by nvidia
        elif technique == "FXAA":
            self.antialiasingPass = AntialiasingFXAAPass()
            
        # SMAA T2
        elif technique == "SMAA":
            self.antialiasingPass = AntialiasingSMAAPass()
            self.jitter = True

            # Extract smaa quality preset and define it in the shader
            quality = self.pipeline.settings.smaaQuality.upper()
            if quality in ["LOW", "MEDIUM", "HIGH", "ULTRA"]:
                self.pipeline.getRenderPassManager().registerDefine("SMAA_PRESET_" + quality, 1)
            else:
                self.error("Unrecognized SMAA quality:", quality)
                return

        # When jittering is enabled, precompute the jitter offsets
        if self.jitter:

            # Compute how big a pixel is on screen
            onePixelShift = Vec2(0.5 / float(self.pipeline.getSize().x), 
                0.5 / float(self.pipeline.getSize().y)) * self.pipeline.settings.jitterAmount * 0.5

            # Annoying that Vec2 has no multliply-operator for non-floats
            multiplyVec2 = lambda a, b: Vec2(a.x*b.x, a.y*b.y)

            # Multiply the pixel size with the offsets to compute the final jitter
            self.jitterOffsets = [
                multiplyVec2(onePixelShift, Vec2(-0.25,  0.25)),
                multiplyVec2(onePixelShift, Vec2(0.25, -0.25))
            ]


        # Finally register the antialiasing pass
        self.pipeline.getRenderPassManager().registerPass(self.antialiasingPass)

    def update(self):
        """ Updates the manager, setting the jitter offsets if enabled """
        if self.jitter:
            shift = self.jitterOffsets[self.jitterIndex]
            self.jitterIndex = 1 - self.jitterIndex
            Globals.base.camLens.setFilmOffset(shift.x, shift.y)

