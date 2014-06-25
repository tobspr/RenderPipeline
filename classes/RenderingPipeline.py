
import math
from panda3d.core import TransparencyAttrib, Texture, Vec2, ComputeNode

from LightManager import LightManager
from RenderTarget import RenderTarget
from RenderTargetType import RenderTargetType
from DebugObject import DebugObject
from BetterShader import BetterShader


class RenderingPipeline(DebugObject):

    def __init__(self, showbase):
        DebugObject.__init__(self, "RenderingPipeline")
        self.showbase = showbase
        self.lightManager = LightManager()
        self.size = self._getSize()
        self.camera = base.cam
        self.cullBounds = None
        self.patchSize = (8, 8)
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
        self.deferredTarget.getQuad().setShader(BetterShader.load(
            "Shader/DefaultPostProcess.vertex", "Shader/TextureDisplay.fragment"))
        self.deferredTarget.getQuad().setShaderInput(
            "sampler", self.lightingPassTex)
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
        sizeX = int(math.ceil(self.size.x / self.patchSize[0]))
        sizeY = int(math.ceil(self.size.y / self.patchSize[1]))

        self.debug("Batch size =", sizeX, "x", sizeY,
                   "Buffer size=", sizeX * self.patchSize[0], "x", sizeY * self.patchSize[1])

        # Create a buffer which computes the min / max bounds
        self._makePositionComputationBuffer(sizeX, sizeY)

        # create a texture where the light shader can write to
        self.lightingPassTex = Texture("LightingPassResult")
        self.lightingPassTex.setup2dTexture(
            sizeX * self.patchSize[0], sizeY * self.patchSize[1], Texture.TFloat, Texture.FRgba8)
        self.lightingPassTex.setMinfilter(Texture.FTNearest)
        self.lightingPassTex.setMagfilter(Texture.FTNearest)
        # self.lightingPassTex.clearRamImage() # doesn't work

        # create compute node
        self.lightingComputeNode = ComputeNode("LightingComputePass")
        self.lightingComputeNode.add_dispatch(sizeX, sizeY, 1)

        # attach compute node to scene graph
        self.lightingComputeContainer = render.attachNewNode(
            self.lightingComputeNode)
        self.lightManager.setComputeShaderNode(self.lightingComputeContainer)

        # Set scene data as shader input
        self.lightingComputeContainer.setShaderInput(
            "destinationImage", self.lightingPassTex)
        self.lightingComputeContainer.setShaderInput(
            "target0Image", self.deferredTarget.getTexture(RenderTargetType.Color))
        self.lightingComputeContainer.setShaderInput(
            "target1Image", self.deferredTarget.getTexture(RenderTargetType.Aux0))
        self.lightingComputeContainer.setShaderInput(
            "target2Image", self.deferredTarget.getTexture(RenderTargetType.Aux1))

        # Ensure the images have the correct filter mode
        for bmode in [RenderTargetType.Color]:
            tex = self.posComputeBuff.getTexture(bmode)
            tex.setMinfilter(Texture.FTNearest)
            tex.setMagfilter(Texture.FTNearest)

        self.lightingComputeContainer.setShaderInput(
            "minMaxDepthImage", self.posComputeBuff.getTexture(RenderTargetType.Color))

        # pass render and camera to allow reprojection of depth
        self.lightingComputeContainer.setShaderInput("render", render)
        self.lightingComputeContainer.setShaderInput(
            "camera", self.showbase.cam)

        self.lightingComputeContainer.setBin("unsorted", 10)

        self._loadFallbackCubemap()

        self.posComputeBuff.getQuad().setShaderInput(
            "position", self.deferredTarget.getTexture(RenderTargetType.Aux1))

        self.posComputeBuff.getQuad().setShaderInput(
            "depth", self.deferredTarget.getTexture(RenderTargetType.Depth))

    def _loadFallbackCubemap(self):
        cubemap = loader.loadCubeMap("Cubemap/#.png")
        cubemap.setMinfilter(Texture.FTLinearMipmapLinear)
        cubemap.setMagfilter(Texture.FTLinearMipmapLinear)
        cubemap.setFormat(Texture.F_srgb_alpha)
        self.lightingComputeContainer.setShaderInput(
            "fallbackCubemap", cubemap)

    def _makePositionComputationBuffer(self, w, h):
        self.debug("Creating position computation buffer")
        self.posComputeBuff = RenderTarget("PositionPrecompute")
        self.posComputeBuff.setSize(w, h)
        self.posComputeBuff.addRenderTexture(RenderTargetType.Color)
        self.posComputeBuff.setColorBits(16)
        self.posComputeBuff.prepareOffscreenBuffer()
        self._setPositionComputationShader()

    def _setPositionComputationShader(self):
        pcShader = BetterShader.load(
            "Shader/DefaultPostProcess.vertex", "Shader/PrecomputeMinMaxPos.fragment")
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

        self.lightingComputeContainer.setShaderInput(
            "cameraPosition", self.showbase.cam.getPos(render))

        return task.cont

    def getLightManager(self):
        return self.lightManager

    def getDefaultObjectShader(self):
        shader = BetterShader.load(
            "Shader/DefaultObjectShader.vertex", "Shader/DefaultObjectShader.fragment")
        return shader
