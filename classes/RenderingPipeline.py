
import math
from panda3d.core import TransparencyAttrib, Texture, Vec2, NodePath
from panda3d.core import Mat4, CSYupRight, TransformState, CSZupRight, LVecBase2i

from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.DirectGui import DirectFrame


from LightManager import LightManager
from RenderTarget import RenderTarget
from RenderTargetType import RenderTargetType
from DebugObject import DebugObject
from BetterShader import BetterShader
from Antialiasing import Antialiasing
from PipelineSettingsManager import PipelineSettingsManager

# Render Pipeline
class RenderingPipeline(DebugObject):

    def __init__(self, showbase):
        DebugObject.__init__(self, "RenderingPipeline")
        self.showbase = showbase
        self.settings = None

    def loadSettings(self, filename):
        self.settings = PipelineSettingsManager()
        self.settings.loadFromFile(filename)

    def create(self):
        self.debug("Setting up render pipeline")

        if self.settings is None:
            self.error("You have to call loadSettings first!")
            return

        self.camera = base.cam
        self.size = self._getSize()
        self.cullBounds = None
        self.temporalProjXOffs = 0
        self.temporalProjFactor = 2
        self.lightManager = LightManager()
        self.patchSize = Vec2(
            self.settings['computePatchSizeX'], self.settings['computePatchSizeY'])
        self.lastMVP = None

        self.forwardScene = NodePath("Forward-Rendering")
        self.transparencyScene = NodePath("Transparency-Rendering")

        # First, we need no transparency
        render.setAttrib(
            TransparencyAttrib.make(TransparencyAttrib.MNone), 100)

        # Now create deferred render buffers
        self._makeDeferredTargets()

        # Setup compute shader for lighting
        self._createLightingPipeline()

        # Setup combiner
        self._createCombiner()

        self.deferredTarget.setShader(BetterShader.load(
            "Shader/DefaultPostProcess.vertex", "Shader/TextureDisplay.fragment"))
        self._setupAntialiasing()

        self._createFinalPass()

        self.antialias.getFirstBuffer().setShaderInput(
            "lastFrame", self.lightingComputeCombinedTex)
        self.antialias.getFirstBuffer().setShaderInput(
            "lastPosition", self.lastPositionBuffer)
        self.antialias.getFirstBuffer().setShaderInput(
            "currentPosition", self.deferredTarget.getColorTexture())

        self.deferredTarget.setShaderInput(
            "sampler", self.finalPass.getColorTexture())
        # self.deferredTarget.setShaderInput("sampler", self.combiner.getColorTexture())

        # self.deferredTarget.setShaderInput("sampler", self.lightingComputeCombinedTex)
        # self.deferredTarget.setShaderInput("sampler", self.antialias._neighborBuffer.getColorTexture())
        # self.deferredTarget.setShaderInput("sampler", self.antialias._blendBuffer.getColorTexture())
        # self.deferredTarget.setShaderInput("sampler", self.lightingComputeCombinedTex)

        # add update task
        self._attachUpdateTask()

        # compute first mvp
        self._computeMVP()
        self.lastLastMVP = self.lastMVP

        # DirectFrame(frameColor=(1, 1, 1, 0.2), frameSize=(-0.28, 0.28, -0.27, 0.4), pos=(base.getAspectRatio() - 0.35, 0.0, 0.49))
        self.atlasDisplayImage = OnscreenImage(image=self.lightManager.getAtlasTex(), pos=(
            base.getAspectRatio() - 0.35, 0, 0.5), scale=(0.25, 0, 0.25))
        # self.lastPosImage = OnscreenImage(image=self.lightingComputeCombinedTex, pos=(
        #     base.getAspectRatio() - 0.35, 0, -0.05), scale=(0.25, 0, 0.25))
        # self.atlasDisplayImage =  OnscreenImage(image = self.lightManager.getAtlasTex(), pos = (0,0,0), scale=(0.8,1,0.8))
        # self.atlasDisplayImage =  OnscreenImage(image = self.lightPerTileStorage, pos = (base.getAspectRatio() - 0.35, 0, 0.5), scale=(0.25,0,0.25))

    def _createCombiner(self):
        self.combiner = RenderTarget("Combine-Temporal")
        self.combiner.setColorBits(8)
        self.combiner.addRenderTexture(RenderTargetType.Color)
        self.combiner.prepareOffscreenBuffer()
        self.combiner.setShaderInput(
            "currentComputation", self.lightingComputeContainer.getColorTexture())
        self.combiner.setShaderInput(
            "lastFrame", self.lightingComputeCombinedTex)
        self.combiner.setShaderInput(
            "positionBuffer", self.deferredTarget.getColorTexture())
        self.combiner.setShaderInput(
            "velocityBuffer", self.deferredTarget.getAuxTexture(1))
        self.combiner.setShaderInput("lastPosition", self.lastPositionBuffer)

        self._setCombinerShader()

    def _setupAntialiasing(self):
        self.debug("Creating antialiasing handler ..")
        self.antialias = Antialiasing()

        # self.antialias.setColorTexture(self.lightingComputeContainer.getColorTexture())
        self.antialias.setColorTexture(self.combiner.getColorTexture())
        self.antialias.setDepthTexture(self.deferredTarget.getDepthTexture())
        self.antialias.setup()

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
        # self.deferredTarget.setSize(400, 240) # check for overdraw
        self.deferredTarget.prepareSceneRender()

    def _createFinalPass(self):
        self.debug("Creating final pass")
        self.finalPass = RenderTarget("FinalPass")
        self.finalPass.addRenderTexture(RenderTargetType.Color)
        self.finalPass.prepareOffscreenBuffer()

        colorTex = self.antialias.getResultTexture()
        # Set wrap for motion blur
        colorTex.setWrapU(Texture.WMMirror)
        colorTex.setWrapV(Texture.WMMirror)
        self.finalPass.setShaderInput("colorTex", colorTex)
        self.finalPass.setShaderInput(
            "velocityTex", self.deferredTarget.getAuxTexture(1))
        self.finalPass.setShaderInput(
            "depthTex", self.deferredTarget.getDepthTexture())
        self._setFinalPassShader()

    # Creates the storage to store the list of visible lights per tile
    def _makeLightPerTileStorage(self):

        storageSizeX = int(self.precomputeSize.x * 8)
        storageSizeY = int(self.precomputeSize.y * 8)

        self.debug(
            "Creating per tile storage of size", storageSizeX, "x", storageSizeY)

        self.lightPerTileStorage = Texture("LightsPerTile")
        self.lightPerTileStorage.setup2dTexture(
            storageSizeX, storageSizeY, Texture.TUnsignedShort, Texture.FR32i)
        self.lightPerTileStorage.setMinfilter(Texture.FTNearest)
        self.lightPerTileStorage.setMagfilter(Texture.FTNearest)

    # Inits the lighting pipeline
    def _createLightingPipeline(self):
        self.debug("Creating lighting pipeline ..")

        # size has to be a multiple of the compute unit size
        # but still has to cover the whole screen
        sizeX = int(math.ceil(self.size.x / self.patchSize.x))
        sizeY = int(math.ceil(self.size.y / self.patchSize.y))

        self.precomputeSize = Vec2(sizeX, sizeY)

        self.debug("Batch size =", sizeX, "x", sizeY,
                   "Actual Buffer size=", int(sizeX * self.patchSize.x), "x", int(sizeY * self.patchSize.y))

        self._makeLightPerTileStorage()

         # Create a buffer which computes which light affects which tile
        self._makeLightBoundsComputationBuffer(sizeX, sizeY)

        # Create a buffer which applies the lighting
        self._makeLightingComputeBuffer()

        # Register for light manager
        self.lightManager.setLightingComputator(self.lightingComputeContainer)
        self.lightManager.setLightingCuller(self.lightBoundsComputeBuff)

        self.lightingComputeContainer.setShaderInput(
            "lightsPerTile", self.lightPerTileStorage)

        self.lightingComputeContainer.setShaderInput(
            "cameraPosition", base.cam.getPos(render))

        # Ensure the images have the correct filter mode
        for bmode in [RenderTargetType.Color]:
            tex = self.lightBoundsComputeBuff.getTexture(bmode)
            tex.setMinfilter(Texture.FTNearest)
            tex.setMagfilter(Texture.FTNearest)

        self._loadFallbackCubemap()

        # Create storage for the bounds computation

        # Set inputs
        self.lightBoundsComputeBuff.setShaderInput(
            "destination", self.lightPerTileStorage)
        self.lightBoundsComputeBuff.setShaderInput(
            "depth", self.deferredTarget.getDepthTexture())

        self.lightingComputeContainer.setShaderInput(
            "data0", self.deferredTarget.getColorTexture())
        self.lightingComputeContainer.setShaderInput(
            "data1", self.deferredTarget.getAuxTexture(0))
        self.lightingComputeContainer.setShaderInput(
            "data2", self.deferredTarget.getAuxTexture(1))

        self.lightingComputeContainer.setShaderInput(
            "shadowAtlas", self.lightManager.getAtlasTex())
        self.lightingComputeContainer.setShaderInput(
            "destination", self.lightingComputeCombinedTex)
        # self.lightingComputeContainer.setShaderInput("sampleTex", loader.loadTexture("Data/Antialiasing/Unigine01.png"))

    def _loadFallbackCubemap(self):
        cubemap = loader.loadCubeMap("Cubemap/#.png")
        cubemap.setMinfilter(Texture.FTLinearMipmapLinear)
        cubemap.setMagfilter(Texture.FTLinearMipmapLinear)
        cubemap.setFormat(Texture.F_srgb_alpha)
        self.lightingComputeContainer.setShaderInput(
            "fallbackCubemap", cubemap)

    def _makeLightBoundsComputationBuffer(self, w, h):
        self.debug("Creating light precomputation buffer of size", w, "x", h)
        self.lightBoundsComputeBuff = RenderTarget("ComputeLightTileBounds")
        self.lightBoundsComputeBuff.setSize(w, h)
        self.lightBoundsComputeBuff.addRenderTexture(RenderTargetType.Color)
        self.lightBoundsComputeBuff.setColorBits(16)
        self.lightBoundsComputeBuff.prepareOffscreenBuffer()

        self.lightBoundsComputeBuff.setShaderInput("mainCam", base.cam)
        self.lightBoundsComputeBuff.setShaderInput("mainRender", base.render)

        self._setPositionComputationShader()

    def _makeLightingComputeBuffer(self):
        self.lightingComputeContainer = RenderTarget("ComputeLighting")
        self.lightingComputeContainer.setSize(
            base.win.getXSize() / self.temporalProjFactor,  base.win.getYSize())
        self.lightingComputeContainer.addRenderTexture(RenderTargetType.Color)
        self.lightingComputeContainer.setColorBits(16)
        self.lightingComputeContainer.prepareOffscreenBuffer()

        self.lightingComputeCombinedTex = Texture("Lighting-Compute-Combined")
        self.lightingComputeCombinedTex.setup2dTexture(
            base.win.getXSize(), base.win.getYSize(), Texture.TFloat, Texture.FRgba16)
        self.lightingComputeCombinedTex.setMinfilter(Texture.FTLinear)
        self.lightingComputeCombinedTex.setMagfilter(Texture.FTLinear)

        self.lastPositionBuffer = Texture("Last-Position-Buffer")
        self.lastPositionBuffer.setup2dTexture(
            base.win.getXSize(), base.win.getYSize(), Texture.TFloat, Texture.FRgba16)
        self.lastPositionBuffer.setMinfilter(Texture.FTNearest)
        self.lastPositionBuffer.setMagfilter(Texture.FTNearest)

    def _setLightingShader(self):

        lightShader = BetterShader.load(
            "Shader/DefaultPostProcess.vertex", "Shader/ApplyLighting.fragment")
        self.lightingComputeContainer.setShader(lightShader)

    def _setCombinerShader(self):
        cShader = BetterShader.load(
            "Shader/DefaultPostProcess.vertex", "Shader/Combiner.fragment")
        self.combiner.setShader(cShader)

    def _setPositionComputationShader(self):
        pcShader = BetterShader.load(
            "Shader/DefaultPostProcess.vertex", "Shader/PrecomputeLights.fragment")
        self.lightBoundsComputeBuff.setShader(pcShader)

    def _setFinalPassShader(self):
        fShader = BetterShader.load(
            "Shader/DefaultPostProcess.vertex", "Shader/Final.fragment")
        self.finalPass.setShader(fShader)

    def _getSize(self):
        return Vec2(
            int(self.showbase.win.getXSize()),
            int(self.showbase.win.getYSize()))

    def debugReloadShader(self):
        self.lightManager.debugReloadShader()
        self._setPositionComputationShader()
        self._setCombinerShader()
        self._setLightingShader()
        self._setFinalPassShader()
        self.antialias.reloadShader()

    def _attachUpdateTask(self):
        self.showbase.addTask(
            self._update, "UpdateRenderingPipeline", sort=-10000)

    def _computeCameraBounds(self):
        # compute camera bounds in render space
        cameraBounds = self.camera.node().getLens().makeBounds()
        cameraBounds.xform(self.camera.getMat(render))
        return cameraBounds

    def _update(self, task=None):

        self.temporalProjXOffs += 1
        self.temporalProjXOffs = self.temporalProjXOffs % self.temporalProjFactor

        self.cullBounds = self._computeCameraBounds()

        self.lightManager.setCullBounds(self.cullBounds)
        self.lightManager.update()

        self.lightingComputeContainer.setShaderInput(
            "cameraPosition", base.cam.getPos(render))
        self.lightingComputeContainer.setShaderInput(
            "temporalProjXOffs", LVecBase2i(self.temporalProjXOffs))
        self.combiner.setShaderInput("lastMVP", self.lastMVP)
        render.setShaderInput("lastMVP", self.lastMVP)
        self.combiner.setShaderInput(
            "temporalProjXOffs", LVecBase2i(self.temporalProjXOffs))
        self._computeMVP()
        self.combiner.setShaderInput("currentMVP", self.lastMVP)

        self.combiner.setShaderInput("cameraPosition", base.cam.getPos(render))

        if task is not None:
            return task.cont

    def _computeMVP(self):
        projMat = Mat4.convertMat(
            CSYupRight,
            base.camLens.getCoordinateSystem()) * base.camLens.getProjectionMat()
        transformMat = TransformState.makeMat(
            Mat4.convertMat(base.win.getGsg().getInternalCoordinateSystem(),
                            CSZupRight))
        modelViewMat = transformMat.invertCompose(
            render.getTransform(base.cam)).getMat()
        self.lastMVP = modelViewMat * projMat
        # print "Self.lastMVP is now from frame",globalClock.getFrameTime()

    def getLightManager(self):
        return self.lightManager

    def getDefaultObjectShader(self):
        shader = BetterShader.load(
            "Shader/DefaultObjectShader.vertex", "Shader/DefaultObjectShader.fragment")
        return shader
