
from panda3d.core import Texture

from DebugObject import DebugObject
from RenderTarget import RenderTarget
from RenderTargetType import RenderTargetType
from BetterShader import BetterShader

class Antialiasing(DebugObject):

    def __init__(self):
        DebugObject.__init__(self, "Antialiasing")
        self._colorTexture = None
        self._depthTexture = None

    def setDepthTexture(self, tex):
        self._depthTexture = tex

    def setColorTexture(self, tex):
        self._colorTexture = tex

    def setup(self):      
        #  1. The first step is to create two RGBA temporal render targets for holding
        #|edgesTex| and |blendTex|.
        self._setupEdgesBuffer()
        self._setupBlendBuffer()
        self._setupNeighborBuffer()

        self.reloadShader()

        #  2. Both temporal render targets |edgesTex| and |blendTex| must be cleared
        #     each frame. Do not forget to clear the alpha channel!

        self._edgesBuffer.setClearColor()
        self._blendBuffer.setClearColor()

        #  3. The next step is loading the two supporting precalculated textures,
        #     'areaTex' and 'searchTex'. You'll find them in the 'Textures' folder as
        #     C++ headers, and also as regular DDS files. They'll be needed for the
        #     'SMAABlendingWeightCalculation' pass.
        self.areaTex = loader.loadTexture("Data/Antialiasing/AreaTexGL.png")
        self.searchTex = loader.loadTexture("Data/Antialiasing/SearchTexGL.png")

        #  4. All samplers must be set to linear filtering and clamp.
        for sampler in [self.areaTex, self.searchTex, self._edgesBuffer.getColorTexture(), self._blendBuffer.getColorTexture()]:
                sampler.setMinfilter(Texture.FTLinear)
                sampler.setMagfilter(Texture.FTLinear)
                sampler.setWrapU(Texture.WMClamp)
                sampler.setWrapV(Texture.WMClamp)

        self._edgesBuffer.setShaderInput("colorTex", self._colorTexture)
        self._edgesBuffer.setShaderInput("depthTex", self._depthTexture)

        self._blendBuffer.setShaderInput("edgesTex", self._edgesBuffer.getColorTexture())
        self._blendBuffer.setShaderInput("areaTex", self.areaTex)
        self._blendBuffer.setShaderInput("searchTex", self.searchTex)

        self._neighborBuffer.setShaderInput("colorTex", self._colorTexture)
        self._neighborBuffer.setShaderInput("blendTex", self._blendBuffer.getColorTexture())

    def reloadShader(self):
        edgeShader = BetterShader.load("Shader/SMAA-EdgeDetection.vertex", "Shader/SMAA-EdgeDetection.fragment")
        self._edgesBuffer.setShader(edgeShader)

        weightsShader = BetterShader.load("Shader/SMAA-BlendingWeights.vertex", "Shader/SMAA-BlendingWeights.fragment")
        self._blendBuffer.setShader(weightsShader)

        neighborShader = BetterShader.load("Shader/SMAA-Neighbors.vertex", "Shader/SMAA-Neighbors.fragment")
        self._neighborBuffer.setShader(neighborShader)


    def _setupEdgesBuffer(self):
        self._edgesBuffer = RenderTarget("SMAA-Edges")
        self._edgesBuffer.addRenderTexture(RenderTargetType.Color)
        # self._edgesBuffer.setColorBits(16)
        self._edgesBuffer.prepareOffscreenBuffer()      

    def _setupBlendBuffer(self):
        self._blendBuffer = RenderTarget("SMAA-Blend")
        self._blendBuffer.addRenderTexture(RenderTargetType.Color)
        # self._blendBuffer.setColorBits(16)
        self._blendBuffer.prepareOffscreenBuffer()      

    def _setupNeighborBuffer(self):
        self._neighborBuffer = RenderTarget("SMAA-Neighbors")
        self._neighborBuffer.addRenderTexture(RenderTargetType.Color)
        # self._blendBuffer.setColorBits(16)
        self._neighborBuffer.prepareOffscreenBuffer()
        # self._neighborBuffer.setClearColor()
