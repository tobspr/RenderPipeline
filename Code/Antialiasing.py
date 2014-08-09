
from panda3d.core import Texture, PTAInt

from DebugObject import DebugObject
from RenderTarget import RenderTarget
from RenderTargetType import RenderTargetType
from BetterShader import BetterShader
from Globals import Globals
from AbstractMethodException import AbstractMethodException

__all__ = [
    "AntialiasingTechniqueNone",
    "AntialiasingTechniqueSMAA",
    "AntialiasingTechniqueFXAA"
]


class AntialiasingTechnique(DebugObject):

    """ Abstract aliasing class. All supported aliasing
    methods have to implement the methods this class
    defines. The sense of this class is to make it easy
    to integrate new antialiasing solutions """

    def __init__(self, techniqueName):
        """ Subclasses have to call this. techniqueName should be
        something like "SMAA" """
        DebugObject.__init__(self, "Antialiasing-" + techniqueName)
        self._colorTexture = None
        self._depthTexture = None
        self._velocityTexture = None

    def setDepthTexture(self, tex):
        """ Sets the depth texture which the antialiasing will use
        for edge detection """
        self._depthTexture = tex

    def setColorTexture(self, tex):
        """ Sets the color texture which the antialiasing will use
        for edge detection and displaying the final result"""
        self._colorTexture = tex

    def setVelocityTexture(self, texture):
        """ Sets the texture where the per-vertex velocity is encoded """
        self._velocityTexture = texture

    def getResultTexture(self):
        """ Subclasses should implement this, and return the final
        result of the aliasing, which the pipeline continues to
        work with """
        raise AbstractMethodException()

    def setup(self):
        """ Subclasses should implement this, and create the
        needed RenderTargets and Shaders here """
        raise AbstractMethodException()

    def reloadShader(self):
        """ Subclasses should implement this, and reload all their
        shaders """
        raise AbstractMethodException()

    def requiresJittering(self):
        """ Wheter to render with subpixel offsets """
        raise AbstractMethodException()

    def preRenderUpdate(self):
        """ Called before actuall rendering gets done. Antialiasing can modify
        render targets at this time. Child classes don't have to implement
        this """
        pass

    def postRenderUpdate(self):
        """ Called after rendering was performed. Child classes don't have to
        implement this """
        pass


class AntialiasingTechniqueNone(AntialiasingTechnique):

    """ Technique which does no anti-aliasing. """

    def __init__(self):
        AntialiasingTechnique.__init__(self, "NoAntiAliasing")

    def setup(self):
        """ Does nothing """

    def reloadShader(self):
        """ Does nothing """

    def getFirstBuffer(self):
        """ Returns the first buffer, see AntialiasingTechnique """
        return None

    def getResultTexture(self):
        """ Returns the result texture, see AntialiasingTechnique """
        return self._colorTexture

    def requiresJittering(self):
        """ Not required """
        return False


class AntialiasingTechniqueFXAA(AntialiasingTechnique):

    """ FXAA 3.11 by NVIDIA """

    def __init__(self):
        AntialiasingTechnique.__init__(self, "FXAA")

    def setup(self):
        """ only one buffer is required """
        self._buffer = RenderTarget("FXAA")
        self._buffer.addColorTexture()
        self._buffer.prepareOffscreenBuffer()
        self._buffer.setShaderInput("colorTex", self._colorTexture)

    def reloadShader(self):
        """ Reloads all assigned shaders """

        fxaaShader = BetterShader.load("Shader/DefaultPostProcess.vertex",
                                       "Shader/FXAA/FXAA3.fragment")
        self._buffer.setShader(fxaaShader)

    def getResultTexture(self):
        """ Returns the result texture, see AntialiasingTechnique """
        return self._buffer.getColorTexture()

    def requiresJittering(self):
        """ Not required """
        return False


class AntialiasingTechniqueSMAA(AntialiasingTechnique):

    """ SMAA Method from http://www.iryoku.com/smaa/. We only use
    SMAA x1, as we already use temporal reprojection and using T2
    we would be 4 frames behind (too many!!) """

    def __init__(self):
        """ Creates this Technique """
        AntialiasingTechnique.__init__(self, "SMAA")
        self.currentIndex = PTAInt.emptyArray(1)
        self.currentIndex[0] = 0

    def setup(self):
        """ Setups the SMAA. The comments are original from the SMAA.glsl """
        #  1. The first step is to create two RGBA temporal render targets for holding
        #|edgesTex| and |blendTex|.
        self._setupEdgesBuffer()
        self._setupBlendBuffer()
        self._setupNeighborBuffer()
        self._setupResolveBuffer()

        #  2. Both temporal render targets |edgesTex| and |blendTex| must be cleared
        #     each frame. Do not forget to clear the alpha channel!

        self._edgesBuffer.setClearColor()
        self._blendBuffer.setClearColor()

        #  3. The next step is loading the two supporting precalculated textures,
        #     'areaTex' and 'searchTex'. You'll find them in the 'Textures' folder as
        #     C++ headers, and also as regular DDS files. They'll be needed for the
        #     'SMAABlendingWeightCalculation' pass.
        self.areaTex = Globals.loader.loadTexture(
            "Data/Antialiasing/SMAA_AreaTexGL.png")
        self.searchTex = Globals.loader.loadTexture(
            "Data/Antialiasing/SMAA_SearchTexGL.png")

        #  4. All samplers must be set to linear filtering and clamp.
        for sampler in [self.areaTex, self.searchTex, self._edgesBuffer.getColorTexture(), self._blendBuffer.getColorTexture()]:
            sampler.setMinfilter(Texture.FTLinear)
            sampler.setMagfilter(Texture.FTLinear)
            sampler.setWrapU(Texture.WMClamp)
            sampler.setWrapV(Texture.WMClamp)

        self._edgesBuffer.setShaderInput("colorTex", self._colorTexture)
        # self._edgesBuffer.setShaderInput("depthTex", self._depthTexture)

        self._blendBuffer.setShaderInput(
            "edgesTex", self._edgesBuffer.getColorTexture())
        self._blendBuffer.setShaderInput("areaTex", self.areaTex)
        self._blendBuffer.setShaderInput("searchTex", self.searchTex)
        self._blendBuffer.setShaderInput("currentIndex", self.currentIndex)

        for buff in self._neighborBuffers:
            buff.setShaderInput("colorTex", self._colorTexture)
            buff.setShaderInput("velocityTex", self._velocityTexture)
            buff.setShaderInput(
                "blendTex", self._blendBuffer.getColorTexture())

        self._resolveBuffer.setShaderInput(
            "velocityTex", self._velocityTexture)

        # Set initial shader
        self.reloadShader()

    def reloadShader(self):
        """ Reloads all used shaders """
        edgeShader = BetterShader.load(
            "Shader/SMAA/EdgeDetection.vertex", "Shader/SMAA/EdgeDetection.fragment")
        self._edgesBuffer.setShader(edgeShader)

        weightsShader = BetterShader.load(
            "Shader/SMAA/BlendingWeights.vertex", "Shader/SMAA/BlendingWeights.fragment")
        self._blendBuffer.setShader(weightsShader)

        neighborShader = BetterShader.load(
            "Shader/SMAA/Neighbors.vertex", "Shader/SMAA/Neighbors.fragment")

        for buff in self._neighborBuffers:
            buff.setShader(neighborShader)

        resolveShader = BetterShader.load(
            "Shader/SMAA/Resolve.vertex", "Shader/SMAA/Resolve.fragment")
        self._resolveBuffer.setShader(resolveShader)

    def getResultTexture(self):
        """ Returns the result texture, see AntialiasingTechnique """
        return self._resolveBuffer.getColorTexture()

    def _setupEdgesBuffer(self):
        """ Internal method to create the edges buffer """
        self._edgesBuffer = RenderTarget("SMAA-Edges")
        self._edgesBuffer.addRenderTexture(RenderTargetType.Color)
        self._edgesBuffer.prepareOffscreenBuffer()

    def _setupBlendBuffer(self):
        """ Internal method to create the blending buffer """
        self._blendBuffer = RenderTarget("SMAA-Blend")
        self._blendBuffer.addRenderTexture(RenderTargetType.Color)
        self._blendBuffer.prepareOffscreenBuffer()

    def _setupNeighborBuffer(self):
        """ Internal method to create the weighting buffer """

        self._neighborBuffers = []
        for i in xrange(2):
            self._neighborBuffers.append(RenderTarget("SMAA-Neighbors"))
            self._neighborBuffers[i].addRenderTexture(RenderTargetType.Color)
            self._neighborBuffers[i].prepareOffscreenBuffer()

    def _setupResolveBuffer(self):
        """ Creates the buffer which does the final resolve pass """
        self._resolveBuffer = RenderTarget("SMAA-Resolve")
        self._resolveBuffer.addColorTexture()
        self._resolveBuffer.prepareOffscreenBuffer()

    def requiresJittering(self):
        """ For SMAA T2 """
        return True

    def preRenderUpdate(self):
        """ Selects the correct buffers """

        self._neighborBuffers[self.currentIndex[0]].setActive(False)
        self._resolveBuffer.setShaderInput("lastTex",
                                           self._neighborBuffers[self.currentIndex[0]].getColorTexture())

        self.currentIndex[0] = 1 - self.currentIndex[0]
        self._neighborBuffers[self.currentIndex[0]].setActive(True)

        self._resolveBuffer.setShaderInput("currentTex",
                                           self._neighborBuffers[self.currentIndex[0]].getColorTexture())
