

from panda3d.core import Shader, Texture, SamplerState, GeomEnums, Vec4

from DebugObject import DebugObject
from Globals import Globals
from RenderTarget import RenderTarget
from MemoryMonitor import MemoryMonitor
from RenderPasses.TransparencyPass import TransparencyPass

class TransparencyManager(DebugObject):

    """ This class manages rendering of transparency. It creates the buffers to
    store transparency data in, and also provides the default transparency shader.

    Internal OIT is used, with per pixel linked lists. The sorting happens in the
    final transparency pass. """

    def __init__(self, pipeline):
        """ Creates the manager, but does not init the buffers """
        DebugObject.__init__(self, "TransparencyManager")
        self.debug("Initializing ..")

        self.pipeline = pipeline

        # This stores the maximum amount of transparent pixels which can be on the
        # screen at one time. If the amount of pixels exceeds this value, strong
        # artifacts will occur!
        self.maxPixelCount = 1920 * 1080 * 2
        self.initTransparencyPass()

    def initTransparencyPass(self):
        """ Creates the pass which renders the transparent objects into the scene """
        self.transparencyPass = TransparencyPass()
        self.pipeline.getRenderPassManager().registerPass(self.transparencyPass)

        # Create the atomic counter which stores the amount of rendered transparent
        # pixels. For now this a 1x1 texture, as atomic counters are not implemented.
        self.pixelCountBuffer = Texture("MaterialCountBuffer")
        self.pixelCountBuffer.setup2dTexture(1, 1, Texture.TInt, Texture.FR32i)

        # Creates the buffer which stores all transparent pixels. Pixels are inserted
        # into the buffer in the order they are rendered, using the pixelCountBuffer
        # to determine their index 
        self.materialDataBuffer = Texture("MaterialDataBuffer")
        self.materialDataBuffer.setupBufferTexture(self.maxPixelCount, Texture.TFloat, 
            Texture.FRgba32, GeomEnums.UH_static)

        # Creates the list head buffer, which stores the first transparent pixel for
        # each window pixel. The index stored in this buffer is the index into the 
        # materialDataBuffer
        self.listHeadBuffer = Texture("ListHeadBuffer")
        self.listHeadBuffer.setup2dTexture(self.pipeline.getSize().x, self.pipeline.getSize().y, 
            Texture.TInt, Texture.FR32i)

        # Creates the spinlock buffer, which ensures that writing to the listHeadBuffer
        # is sequentially
        self.spinLockBuffer = Texture("SpinLockBuffer")
        self.spinLockBuffer.setup2dTexture(self.pipeline.getSize().x, self.pipeline.getSize().y, 
            Texture.TInt, Texture.FR32i)

        # Set the buffers as input to the main scene. Maybe we can do this more elegant
        target = self.pipeline.showbase.render
        target.setShaderInput("pixelCountBuffer", self.pixelCountBuffer)
        target.setShaderInput("spinLockBuffer", self.spinLockBuffer)
        target.setShaderInput("materialDataBuffer", self.materialDataBuffer)
        target.setShaderInput("listHeadBuffer", self.listHeadBuffer)

        # Provides the buffers as global shader inputs
        self.pipeline.getRenderPassManager().registerStaticVariable("transpPixelCountBuffer", self.pixelCountBuffer)
        self.pipeline.getRenderPassManager().registerStaticVariable("transpSpinLockBuffer", self.spinLockBuffer)
        self.pipeline.getRenderPassManager().registerStaticVariable("transpListHeadBuffer", self.listHeadBuffer)
        self.pipeline.getRenderPassManager().registerStaticVariable("transpMaterialDataBuffer", self.materialDataBuffer)

        # Registers the transparency settings to the shaders
        self.pipeline.getRenderPassManager().registerDefine("USE_TRANSPARENCY", 1)
        self.pipeline.getRenderPassManager().registerDefine("MAX_TRANSPARENCY_LAYERS", 
            self.pipeline.settings.maxTransparencyLayers)

        self.pixelCountBuffer.setClearColor(Vec4(0, 0, 0, 0))
        self.spinLockBuffer.setClearColor(Vec4(0, 0, 0, 0))
        self.listHeadBuffer.setClearColor(Vec4(0, 0, 0, 0))

        MemoryMonitor.addTexture("MaterialCountBuffer", self.pixelCountBuffer)
        MemoryMonitor.addTexture("MaterialDataBuffer", self.materialDataBuffer)
        MemoryMonitor.addTexture("ListHeadBuffer", self.listHeadBuffer)
        MemoryMonitor.addTexture("SpinLockBuffer", self.spinLockBuffer)

    def update(self):
        """ The update method clears the buffers before rendering the next frame """
        self.pixelCountBuffer.clearImage()
        self.spinLockBuffer.clearImage()
        self.listHeadBuffer.clearImage()

    def getDefaultShader(self):
        """ Returns the default shader for transparent objects """
        shader = Shader.load(Shader.SLGLSL, 
                "Shader/DefaultShaders/Transparent/vertex.glsl",
                "Shader/DefaultShaders/Transparent/fragment.glsl")
        return shader

