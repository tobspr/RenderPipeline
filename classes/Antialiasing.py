
from panda3d.core import Texture

from DebugObject import DebugObject
from RenderTarget import RenderTarget
from RenderTargetType import RenderTargetType
from BetterShader import BetterShader
from Globals import Globals


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

    def setDepthTexture(self, tex):
        """ Sets the depth texture which the antialiasing will use
        for edge detection """
        self._depthTexture = tex

    def setColorTexture(self, tex):
        """ Sets the color texture which the antialiasing will use
        for edge detection and displaying the final result"""
        self._colorTexture = tex

    def getFirstBuffer(self):
        """ Subclasses should implement this, and return the first
        antialiasing stage. This is needed, because the first aliasing
        stage also has to copy the position buffer to the last position
        buffer, and same for the color-buffer. """
        raise NotImplementedError()

    def getResultTexture(self):
        """ Subclasses should implement this, and return the final
        result of the aliasing, which the pipeline continues to
        work with """
        raise NotImplementedError()

    def setup(self):
        """ Subclasses should implement this, and create the
        needed RenderTargets and Shaders here """
        raise NotImplementedError()

    def reloadShader(self):
        """ Subclasses should implement this, and reload all their
        shaders """
        raise NotImplementedError()


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



class AntialiasingTechniqueSMAA(AntialiasingTechnique):

    """ SMAA Method from http://www.iryoku.com/smaa/. We only use
    SMAA x1, as we already use temporal reprojection and using T2
    we would be 4 frames behind (too many!!) """

    def __init__(self):
        """ Creates this Technique """
        AntialiasingTechnique.__init__(self, "SMAA")

    def setup(self):
        """ Setups the SMAA. The comments are original from the SMAA.glsl """
        #  1. The first step is to create two RGBA temporal render targets for holding
        #|edgesTex| and |blendTex|.
        self._setupEdgesBuffer()
        self._setupBlendBuffer()
        self._setupNeighborBuffer()

        #  2. Both temporal render targets |edgesTex| and |blendTex| must be cleared
        #     each frame. Do not forget to clear the alpha channel!

        self._edgesBuffer.setClearColor()
        self._blendBuffer.setClearColor()

        #  3. The next step is loading the two supporting precalculated textures,
        #     'areaTex' and 'searchTex'. You'll find them in the 'Textures' folder as
        #     C++ headers, and also as regular DDS files. They'll be needed for the
        #     'SMAABlendingWeightCalculation' pass.
        self.areaTex = Globals.loader.loadTexture("Data/Antialiasing/SMAA_AreaTexGL.png")
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

        self._neighborBuffer.setShaderInput("colorTex", self._colorTexture)
        self._neighborBuffer.setShaderInput(
            "blendTex", self._blendBuffer.getColorTexture())

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
        self._neighborBuffer.setShader(neighborShader)

    def getFirstBuffer(self):
        """ Returns the first buffer, see AntialiasingTechnique """
        return self._edgesBuffer

    def getResultTexture(self):
        """ Returns the result texture, see AntialiasingTechnique """
        return self._neighborBuffer.getColorTexture()

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
        self._neighborBuffer = RenderTarget("SMAA-Neighbors")
        self._neighborBuffer.addRenderTexture(RenderTargetType.Color)
        self._neighborBuffer.prepareOffscreenBuffer()

