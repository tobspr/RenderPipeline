

from panda3d.core import Shader, Texture, SamplerState, GeomEnums, Vec4

from DebugObject import DebugObject
from Globals import Globals
from RenderTarget import RenderTarget

from MemoryMonitor import MemoryMonitor

class TransparencyManager(DebugObject):


    def __init__(self, pipeline):
        DebugObject.__init__(self, "TransparencyManager")
        self.debug("Initializing ..")

        self.pipeline = pipeline
        self.maxPixelCount = 10000000


    def initTransparencyPass(self):
        """ Creates the pass which renders the transparent objects into the scene """
        self.transparencyPass = RenderTarget("TransparencyPass")
        self.transparencyPass.addColorTexture()
        self.transparencyPass.setColorBits(16)
        self.transparencyPass.prepareOffscreenBuffer()
        self.transparencyPass.setClearColor(color=Vec4(0.2,0.5,1.0, 0.0))

        self.pixelCountBuffer = Texture("MaterialCountBuffer")
        self.pixelCountBuffer.setup2dTexture(1, 1, Texture.TInt, Texture.FR32i)


        self.materialDataBuffer = Texture("MaterialDataBuffer")
        self.materialDataBuffer.setupBufferTexture(self.maxPixelCount, Texture.TFloat, Texture.FRgba32, GeomEnums.UH_static)

        self.listHeadBuffer = Texture("ListHeadBuffer")
        self.listHeadBuffer.setup2dTexture(self.pipeline.size.x, self.pipeline.size.y, Texture.TInt, Texture.FR32i)

        self.spinLockBuffer = Texture("SpinLockBuffer")
        self.spinLockBuffer.setup2dTexture(self.pipeline.size.x, self.pipeline.size.y, Texture.TInt, Texture.FR32i)


        target = self.pipeline.showbase.render
        target.setShaderInput("pixelCountBuffer", self.pixelCountBuffer)
        target.setShaderInput("spinLockBuffer", self.spinLockBuffer)
        target.setShaderInput("materialDataBuffer", self.materialDataBuffer)
        target.setShaderInput("listHeadBuffer", self.listHeadBuffer)

        self.transparencyPass.setShaderInput("pixelCountBuffer", self.pixelCountBuffer)
        self.transparencyPass.setShaderInput("spinLockBuffer", self.spinLockBuffer)
        self.transparencyPass.setShaderInput("listHeadBuffer", self.listHeadBuffer)
        self.transparencyPass.setShaderInput("materialDataBuffer", self.materialDataBuffer)

        self.pixelCountBuffer.setClearColor(Vec4(0, 0, 0, 0))
        self.spinLockBuffer.setClearColor(Vec4(0, 0, 0, 0))
        self.listHeadBuffer.setClearColor(Vec4(0, 0, 0, 0))




        MemoryMonitor.addTexture("MaterialCountBuffer", self.pixelCountBuffer)
        MemoryMonitor.addTexture("MaterialDataBuffer", self.materialDataBuffer)
        MemoryMonitor.addTexture("ListHeadBuffer", self.listHeadBuffer)
        MemoryMonitor.addTexture("SpinLockBuffer", self.spinLockBuffer)

    def postRenderCallback(self):

        # Globals.base.graphicsEngine.extractTextureData(self.pixelCountBuffer, Globals.base.win.getGsg())

        self.pixelCountBuffer.clearImage()
        self.spinLockBuffer.clearImage()
        self.listHeadBuffer.clearImage()



    def setColorTexture(self, tex):
        self.transparencyPass.setShaderInput("sceneTex", tex)

    def setDepthTexture(self, tex):
        self.transparencyPass.setShaderInput("depthTex", tex)

    def reloadShader(self):
        self._setTransparencyPassShader()

    def _setTransparencyPassShader(self):
        tShader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/TransparencyPass.fragment")
        self.transparencyPass.setShader(tShader)

    def getDefaultShader(self):
        shader = Shader.load(Shader.SLGLSL, 
                "Shader/DefaultShaders/Transparent/vertex.glsl",
                "Shader/DefaultShaders/Transparent/fragment.glsl")
        return shader

    def getResultTexture(self):
        return self.transparencyPass.getColorTexture()