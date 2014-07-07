
import math
from panda3d.core import TransparencyAttrib, Texture, Vec2, ComputeNode, NodePath
from panda3d.core import Mat4, CSYupRight, TransformState, CSZupRight

from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.DirectGui import DirectFrame


from LightManager import LightManager
from RenderTarget import RenderTarget
from RenderTargetType import RenderTargetType
from DebugObject import DebugObject
from BetterShader import BetterShader
from Antialiasing import Antialiasing


class RenderingPipeline(DebugObject):

    def __init__(self, showbase):
        DebugObject.__init__(self, "RenderingPipeline")
        self.showbase = showbase
        self.lightManager = LightManager()
        self.size = self._getSize()
        self.precomputeSize = Vec2(0)
        self.camera = base.cam
        self.cullBounds = None
        self.patchSize = Vec2(32, 32)

        self.useComputeShader = False
        self.temporalProjXOffs = 0
        self.temporalProjFactor = 2

        self.forwardScene = NodePath("Forward Rendering")
        self.lastMVP = None
        self.lastLastMVP = None

        self._setup()



    def _setup(self):
        self.debug("Setting up render pipeline")
        self.debug("Use compute shaders =",self.useComputeShader)

        # First, we need no transparency
        render.setAttrib(
            TransparencyAttrib.make(TransparencyAttrib.MNone), 100)

        

        # Now create deferred render buffers
        self._makeDeferredTargets()

        # Setup compute shader for lighting
        self._createLightingPipeline()

        # for debugging attach texture to shader
        self.deferredTarget.setShader(BetterShader.load(
            "Shader/DefaultPostProcess.vertex", "Shader/TextureDisplay.fragment"))
        # self.deferredTarget.setShaderInput("sampler", self.lightBoundsComputeBuff.getColorTexture())
        # self.deferredTarget.setShaderInput("sampler", self.lightPerTileStorage)
        self._setupAntialiasing()

        if self.useComputeShader:
            self.deferredTarget.setShaderInput("sampler", self.lightingComputeResult)
        else:
            pass
            # self.deferredTarget.setShaderInput("sampler", self.lightingComputeCombinedTex)
        self.deferredTarget.setShaderInput("sampler", self.antialias.getResultTexture())
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
        self.atlasDisplayImage =  OnscreenImage(image = self.lightManager.getAtlasTex(), pos = (base.getAspectRatio() - 0.35, 0, 0.5), scale=(0.25,0,0.25))
        # self.atlasDisplayImage =  OnscreenImage(image = self.lightPerTileStorage, pos = (base.getAspectRatio() - 0.35, 0, 0.5), scale=(0.25,0,0.25))


    def _setupAntialiasing(self):
        self.debug("Creating antialiasing handler ..")
        self.antialias = Antialiasing()

        # self.antialias.setColorTexture(self.lightingComputeContainer.getColorTexture())
        self.antialias.setColorTexture(self.lightingComputeCombinedTex)
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
        if self.useComputeShader:
            self._makeLightingComputeShader( sizeX, sizeY )

        else:
            self._makeLightingComputeBuffer()

        # Register for light manager
        self.lightManager.setLightingComputator(self.lightingComputeContainer)
        self.lightManager.setLightingCuller(self.lightBoundsComputeBuff)

        self.lightingComputeContainer.setShaderInput(
            "lightsPerTile", self.lightPerTileStorage)

        self.lightingComputeContainer.setShaderInput("cameraPosition", base.cam.getPos(render))

        # Ensure the images have the correct filter mode
        if not self.useComputeShader:
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

        self.lightingComputeContainer.setShaderInput("shadowAtlas", self.lightManager.getAtlasTex())
        self.lightingComputeContainer.setShaderInput("destination", self.lightingComputeCombinedTex)
        self.lightingComputeContainer.setShaderInput("sampleTex", loader.loadTexture("Data/Antialiasing/Unigine01.png"))


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
        self.lightingComputeContainer.setSize(base.win.getXSize() / self.temporalProjFactor,  base.win.getYSize())
        self.lightingComputeContainer.addRenderTexture(RenderTargetType.Color)
        self.lightingComputeContainer.setColorBits(16)
        self.lightingComputeContainer.prepareOffscreenBuffer()

        self.lightingComputeCombinedTex = Texture("Lighting-Compute-Combined")
        self.lightingComputeCombinedTex.setup2dTexture(base.win.getXSize(), base.win.getYSize(), Texture.TFloat, Texture.FRgba16)
        self.lightingComputeCombinedTex.setMinfilter(Texture.FTLinear)
        self.lightingComputeCombinedTex.setMagfilter(Texture.FTLinear)
        self.lightingComputeCombinedTex.setWrapU(Texture.WMMirror)
        self.lightingComputeCombinedTex.setWrapV(Texture.WMMirror)

    def _makeLightingComputeShader(self, sizeX, sizeY):
        
        actualX = int(sizeX * self.patchSize.x)
        actualY = int(sizeY * self.patchSize.y)

        self.lightingComputeResult = Texture("Lighting Compute Result")
        self.lightingComputeResult.setup2dTexture(actualX, actualY, Texture.TFloat, Texture.FRgba16)

        self.lightingComputeNode = ComputeNode("LightingCompute")
        self.lightingComputeNode.addDispatch(sizeX, sizeY, 1)
        self.lightingComputeNP = render.attachNewNode(self.lightingComputeNode)
        self.lightingComputeNP.setBin("unsorted", 20)
        self.lightingComputeNP.setShaderInput("destination", self.lightingComputeResult)

        self.lightingComputeContainer = self.lightingComputeNP


    def _setLightingShader(self):

        if self.useComputeShader:
            lightShader = BetterShader.loadCompute("Shader/ApplyLighting.compute")

        else:
            lightShader = BetterShader.load(
                "Shader/DefaultPostProcess.vertex", "Shader/ApplyLighting.fragment")
        self.lightingComputeContainer.setShader(lightShader)

    def _setPositionComputationShader(self):
        pcShader = BetterShader.load(
            "Shader/DefaultPostProcess.vertex", "Shader/PrecomputeLights.fragment")
        self.lightBoundsComputeBuff.setShader(pcShader)

    def _getSize(self):
        return Vec2(
            int(self.showbase.win.getXSize()),
            int(self.showbase.win.getYSize()))

    def debugReloadShader(self):
        self.lightManager.debugReloadShader()
        self._setPositionComputationShader()
        self._setLightingShader()
        self.antialias.reloadShader()

    def _attachUpdateTask(self):
        self.showbase.addTask(self._update, "UpdateRenderingPipeline",sort=-10000)

    def _computeCameraBounds(self):
        # compute camera bounds in render space
        cameraBounds = self.camera.node().getLens().makeBounds()
        cameraBounds.xform(self.camera.getMat(render))
        return cameraBounds

    def _update(self, task):

        self.temporalProjXOffs += 1
        self.temporalProjXOffs = self.temporalProjXOffs % self.temporalProjFactor

        self.cullBounds = self._computeCameraBounds()

        self.lightManager.setCullBounds(self.cullBounds)
        self.lightManager.update()

        self.lightingComputeContainer.setShaderInput("cameraPosition", base.cam.getPos(render))
        self.lightingComputeContainer.setShaderInput("temporalProjXOffs", float(self.temporalProjXOffs) )


        


        self.lightingComputeContainer.setShaderInput("lastMVP", self.lastLastMVP)
        self.lastLastMVP = self.lastMVP

        self._computeMVP()
        self.lightingComputeContainer.setShaderInput("currentMVP", self.lastMVP)


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
