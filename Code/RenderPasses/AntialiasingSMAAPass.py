
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, PTAFloat, Vec4
from panda3d.core import PTAInt

from Code.Globals import Globals
from Code.RenderPass import RenderPass
from Code.RenderTarget import RenderTarget

class AntialiasingSMAAPass(RenderPass):

    def __init__(self):
        RenderPass.__init__(self)
        self.currentIndex = PTAInt.emptyArray(1)
        self.currentIndex[0] = 0

    def getID(self):
        return "AntialiasingPass"

    def getRequiredInputs(self):
        return {
            "colorTex": ["TransparencyPass.resultTex", "LightingPass.resultTex"],
            "velocityTex": "DeferredScenePass.velocity"
        }

    def create(self):
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

        # self._edgesBuffer.setShaderInput("colorTex", self._colorTexture)
        # self._edgesBuffer.setShaderInput("depthTex", self._depthTexture)

        self._blendBuffer.setShaderInput(
            "edgesTex", self._edgesBuffer.getColorTexture())
        self._blendBuffer.setShaderInput("areaTex", self.areaTex)
        self._blendBuffer.setShaderInput("searchTex", self.searchTex)
        self._blendBuffer.setShaderInput("currentIndex", self.currentIndex)

        for buff in self._neighborBuffers:
            # buff.setShaderInput("colorTex", self._colorTexture)
            # buff.setShaderInput("velocityTex", self._velocityTexture)
            buff.setShaderInput(
                "blendTex", self._blendBuffer.getColorTexture())

        # self._resolveBuffer.setShaderInput(
        #     "velocityTex", self._velocityTexture)


    def setShaders(self):
        edgeShader = Shader.load(Shader.SLGLSL, 
            "Shader/Antialiasing/SMAA/EdgeDetection.vertex", 
            "Shader/Antialiasing/SMAA/EdgeDetection.fragment")
        self._edgesBuffer.setShader(edgeShader)

        weightsShader = Shader.load(Shader.SLGLSL, 
            "Shader/Antialiasing/SMAA/BlendingWeights.vertex", 
            "Shader/Antialiasing/SMAA/BlendingWeights.fragment")
        self._blendBuffer.setShader(weightsShader)

        neighborShader = Shader.load(Shader.SLGLSL, 
            "Shader/Antialiasing/SMAA/Neighbors.vertex", 
            "Shader/Antialiasing/SMAA/Neighbors.fragment")

        for buff in self._neighborBuffers:
            buff.setShader(neighborShader)

        resolveShader = Shader.load(Shader.SLGLSL, 
            "Shader/Antialiasing/SMAA/Resolve.vertex", 
            "Shader/Antialiasing/SMAA/Resolve.fragment")
        self._resolveBuffer.setShader(resolveShader)

    def setShaderInput(self, name, value, *args):
        self._edgesBuffer.setShaderInput(name, value, *args)
        for buff in self._neighborBuffers:
            buff.setShaderInput(name, value, *args)
        self._resolveBuffer.setShaderInput(name, value, *args)
        self._blendBuffer.setShaderInput(name, value, *args)


    def _setupEdgesBuffer(self):
        """ Internal method to create the edges buffer """
        self._edgesBuffer = RenderTarget("SMAA-Edges")
        self._edgesBuffer.addColorTexture()
        self._edgesBuffer.prepareOffscreenBuffer()

    def _setupBlendBuffer(self):
        """ Internal method to create the blending buffer """
        self._blendBuffer = RenderTarget("SMAA-Blend")
        self._blendBuffer.addColorTexture()
        self._blendBuffer.prepareOffscreenBuffer()

    def _setupNeighborBuffer(self):
        """ Internal method to create the weighting buffer """

        self._neighborBuffers = []
        for i in xrange(2):
            self._neighborBuffers.append(RenderTarget("SMAA-Neighbors-" + str(i)))
            self._neighborBuffers[i].addColorTexture()
            self._neighborBuffers[i].prepareOffscreenBuffer()

    def _setupResolveBuffer(self):
        """ Creates the buffer which does the final resolve pass """
        self._resolveBuffer = RenderTarget("SMAA-Resolve")
        self._resolveBuffer.addColorTexture()
        self._resolveBuffer.prepareOffscreenBuffer()

    def preRenderUpdate(self):
        """ Selects the correct buffers """

        self._neighborBuffers[self.currentIndex[0]].setActive(False)
        self._resolveBuffer.setShaderInput("lastTex",
                                           self._neighborBuffers[self.currentIndex[0]].getColorTexture())
        self.currentIndex[0] = 1 - self.currentIndex[0]
        self._neighborBuffers[self.currentIndex[0]].setActive(True)
        self._resolveBuffer.setShaderInput("currentTex",
                                           self._neighborBuffers[self.currentIndex[0]].getColorTexture())

    def getOutputs(self):
        return {
            "AntialiasingPass.resultTex": lambda: self._resolveBuffer.getColorTexture(),
        }

