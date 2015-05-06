

from panda3d.core import PTAVecBase2f, Vec2

from DebugObject import DebugObject
from Globals import Globals

from RenderPasses.AntialiasingFXAAPass import AntialiasingFXAAPass
from RenderPasses.AntialiasingSMAAPass import AntialiasingSMAAPass

class AntialiasingManager(DebugObject):

    availableTechniques = ["FXAA", "SMAA", "NONE"]

    def __init__(self, pipeline):
        DebugObject.__init__(self, "AntialiasingManager")
        self.pipeline = pipeline
        self.jitter = False
        self.jitterOffsets = []
        self.jitterIndex = 0
        self.jitterPTA = PTAVecBase2f.emptyArray(1)
        self.create()

    def create(self):
        self.debug("Creating antialiasing pass")

        technique = self.pipeline.settings.antialiasingTechnique

        if technique not in self.availableTechniques:
            self.error("Unrecognized antialiasing technique: " + technique)
            return

        if technique == "NONE":
            return

        if technique == "FXAA":
            self.aaPass = AntialiasingFXAAPass()
        
        if technique == "SMAA":
            self.aaPass = AntialiasingSMAAPass()
            self.jitter = True


        if self.jitter:
            print self.pipeline.getSize()
            onePixelShift = Vec2(0.5 / float(self.pipeline.getSize().x), 
                0.5 / float(self.pipeline.getSize().y)) * self.pipeline.settings.jitterAmount

            print onePixelShift

            # Annoying that Vec2 has no multliply-operator for non-floats
            multiplyVec2 = lambda a, b: Vec2(a.x*b.x, a.y*b.y)

            self.jitterOffsets = [
                multiplyVec2(onePixelShift, Vec2(-0.25,  0.25)),
                multiplyVec2(onePixelShift, Vec2(0.25, -0.25))
            ]

            print self.jitterOffsets
        self.pipeline.getRenderPassManager().registerPass(self.aaPass)
        # self.pipeline.getRenderPassManager().registerStaticVariable("antialiasingJitterOffset")


    def update(self):
        if self.jitter:
            shift = self.jitterOffsets[self.jitterIndex]
            # print shift
            self.jitterIndex = 1 - self.jitterIndex
            Globals.base.camLens.setFilmOffset(shift.x, shift.y)

