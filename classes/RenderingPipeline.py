
import math
from panda3d.core import Shader, TransparencyAttrib, Texture, Vec2, ComputeNode

from LightManager import LightManager
from RenderTarget import RenderTarget
from RenderTargetType import RenderTargetType
from DebugObject import DebugObject



class RenderingPipeline(DebugObject):

    def __init__(self, showbase):
        DebugObject.__init__(self, "RenderingPipeline")
        self.showbase = showbase
        self.lightManager = LightManager()
        self.size = self._getSize()
        self.camera = base.cam
        self.cullBounds = None
        self._setup()

    def _setup(self):
        self.debug("Setting up render pipeline")

        # First, we need no transparency
        render.setAttrib(
            TransparencyAttrib.make(TransparencyAttrib.MNone), 100)

        # Now create deferred render buffers
        self._makeDeferredTargets()

        # Setup compute shader for lighting
        self._createLightingPipeline()


        # for debugging attach texture to shader
        self.deferredTarget.getQuad().setShader(Shader.load(Shader.SLGLSL, "Shader/DefaultPostProcess.vertex", "Shader/TextureDisplay.fragment"))
        self.deferredTarget.getQuad().setShaderInput("sampler", self.lightingPassTex)
        self.deferredTarget.getQuad().setShaderInput("screenSize", self.size)
        # self.deferredTarget.getQuad().setShaderInput("sampler", self.deferredTarget.getTexture(RenderTargetType.Aux1))

        # add update task
        self._attachUpdateTask()


    # Creates all the render targets
    def _makeDeferredTargets(self):
        self.debug("Creating deferred targets")
        self.deferredTarget = RenderTarget("DeferredTarget")
        self.deferredTarget.addRenderTexture(RenderTargetType.Color)
        self.deferredTarget.addRenderTexture(RenderTargetType.Depth)
        self.deferredTarget.addRenderTexture(RenderTargetType.Aux0)
        self.deferredTarget.addRenderTexture(RenderTargetType.Aux1)
        self.deferredTarget.setAuxBits(16)
        self.deferredTarget.setColorBits(16)
        self.deferredTarget.setDepthBits(32)
        self.deferredTarget.prepareSceneRender()

    # Inits the lighting pipeline
    def _createLightingPipeline(self):
        self.debug("Creating lighting compute shader")

        # size has to be a multiple of the compute unit size
        sizeX = int(math.ceil(self.size.x / 32))
        sizeY = int(math.ceil(self.size.y / 16))

        self.debug("Batch size =",sizeX,"x",sizeY,"Buffer size=", sizeX*32, "x", sizeY*16)

        # Create a buffer which computes the min / max bounds
        self._makePositionComputationBuffer(sizeX, sizeY)

        # create a texture where the light shader can write to
        self.lightingPassTex = Texture("LightingPassResult")
        self.lightingPassTex.setup2dTexture(sizeX*32,sizeY*16, Texture.TFloat, Texture.FRgba8)
        self.lightingPassTex.setMinfilter(Texture.FTNearest)
        self.lightingPassTex.setMagfilter(Texture.FTNearest)
        # self.lightingPassTex.clearRamImage() # doesn't work

        # create compute node
        self.lightingComputeNode = ComputeNode("LightingComputePass")
        self.lightingComputeNode.add_dispatch(sizeX, sizeY, 1)

        # attach compute node to scene graph
        self.lightingComputeContainer = render.attachNewNode(self.lightingComputeNode)
        self.lightManager.setComputeShaderNode(self.lightingComputeContainer)

        # Set scene data as shader input
        self.lightingComputeContainer.setShaderInput("destinationImage", self.lightingPassTex)
        self.lightingComputeContainer.setShaderInput("target0Image", self.deferredTarget.getTexture(RenderTargetType.Color))
        self.lightingComputeContainer.setShaderInput("target1Image", self.deferredTarget.getTexture(RenderTargetType.Aux0))
        self.lightingComputeContainer.setShaderInput("target2Image", self.deferredTarget.getTexture(RenderTargetType.Aux1))

        # Ensure the images have the correct filter mode
        for bmode in [RenderTargetType.Color, RenderTargetType.Aux0]:
            tex = self.posComputeBuff.getTexture(bmode)
            tex.setMinfilter(Texture.FTNearest)
            tex.setMagfilter(Texture.FTNearest)

        self.lightingComputeContainer.setShaderInput("minPositionImage", self.posComputeBuff.getTexture(RenderTargetType.Color))
        self.lightingComputeContainer.setShaderInput("maxPositionImage", self.posComputeBuff.getTexture(RenderTargetType.Aux0))
        self.lightingComputeContainer.setBin("unsorted", 10)

        self._loadFallbackCubemap()

        self.posComputeBuff.getQuad().setShaderInput("position", self.deferredTarget.getTexture(RenderTargetType.Aux1))

    def _loadFallbackCubemap(self):
        cubemap = loader.loadCubeMap("Cubemap/#.png")
        cubemap.setMinfilter(Texture.FTLinearMipmapLinear)
        cubemap.setMagfilter(Texture.FTLinearMipmapLinear)
        cubemap.setFormat(Texture.F_srgb_alpha)
        self.lightingComputeContainer.setShaderInput("fallbackCubemap", cubemap)

    def _makePositionComputationBuffer(self, w, h):
        self.debug("Creating position computation buffer")
        self.posComputeBuff = RenderTarget("DeferredTarget")
        self.posComputeBuff.setSize(w, h)
        self.posComputeBuff.addRenderTexture(RenderTargetType.Color)
        self.posComputeBuff.addRenderTexture(RenderTargetType.Aux0)
        self.posComputeBuff.setColorBits(16)
        self.posComputeBuff.setAuxBits(16)
        self.posComputeBuff.prepareOffscreenBuffer()
        self._setPositionComputationShader()


    def _setPositionComputationShader(self):
        pcShader = Shader.load(Shader.SLGLSL, "Shader/DefaultPostProcess.vertex", "Shader/PrecomputeMinMaxPos.fragment")
        self.posComputeBuff.getQuad().setShader(pcShader)


    def _getSize(self):
        return Vec2(
            int(self.showbase.win.getXSize()),
            int(self.showbase.win.getYSize()))

    def debugReloadShader(self):
        self.lightManager.debugReloadShader()
        self._setPositionComputationShader()

    def _attachUpdateTask(self):
        self.showbase.addTask(self._update, "UpdateRenderingPipeline")

    def _computeCameraBounds(self):
        # compute camera bounds in render space
        cameraBounds = self.camera.node().getLens().makeBounds()
        cameraBounds.xform(self.camera.getMat(render))
        return cameraBounds

    def _update(self, task):
        self.cullBounds = self._computeCameraBounds()

        self.lightManager.setCullBounds(self.cullBounds)
        self.lightManager.update()

        self.lightingComputeContainer.setShaderInput("cameraPosition", self.showbase.cam.getPos(render))

        return task.cont

    def getLightManager(self):
        return self.lightManager

    def getDefaultObjectShader(self):
        shader = Shader.load(
            Shader.SLGLSL, "Shader/DefaultObjectShader.vertex", "Shader/DefaultObjectShader.fragment")
        return shader
