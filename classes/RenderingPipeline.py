
import math
from panda3d.core import TransparencyAttrib, Texture, Vec2, NodePath, PTAInt
from panda3d.core import Mat4, CSYupRight, TransformState, CSZupRight
from panda3d.core import PTAFloat, PTALMatrix4f, UnalignedLMatrix4f, LVecBase2i
from panda3d.core import PTAVecBase3f

from direct.gui.OnscreenImage import OnscreenImage

from LightManager import LightManager
from RenderTarget import RenderTarget
from RenderTargetType import RenderTargetType
from DebugObject import DebugObject
from BetterShader import BetterShader
from Antialiasing import AntialiasingTechniqueSMAA
from PipelineSettingsManager import PipelineSettingsManager


class RenderingPipeline(DebugObject):

    """ This is the core class, driving all other classes. To use this
    pipeline, your code has to call *after* the initialization of ShowBase:

        renderPipeline = RenderingPipeline()
        renderPipeline.loadSettings("pipeline.ini")
        renderPipeline.create()

    The pipeline will setup all required buffers, tasks and shaders itself. To
    add lights, see the documentation of LightManager.

    How it works:

    You can see an example buffer view at http://i.imgur.com/mZK6TVj.png

    The pipeline first renders all normal objects (parented to render) into a
    buffer, using multiple render targets. These buffers store normals,
    position and material properties. Your shaders have to output these
    values, but there is a handy api, just look at
    Shaders/DefaultObjectShader.fragment.

    After that, the pipeline splits the screen into tiles, typically of the
    size 32x32. For each tile, it computes which lights affect which tile,
    called Tiled Deferred Shading. This is written to a buffer.

    The next step is applying the lighting. This is done at half window
    resolution only, using Temporal Reprojection. I don't aim to explain
    Temporal Reprojection here, but basically, I render only each second
    pixel each frame. This is simply for performance.

    The lighting pass iterates through the list of lights per tile, and
    applies both lighting and shadows to each pixel, using the material
    information from the previous rendered buffers.

    After the lighting pass, a combiner pass combines both the current
    frame and the last frame, this is required because of
    Temporal Reprojection.

    At this step, we already have a frame we could display. In the next passes,
    only anti-aliasing and post-processing effects like motion blur are added.

    In the meantime, the LightManager builds a list of ShadowSources which
    need an update. It creates a scene render and renders the scene from the
    view of the shadow sources to the global shadow atlas. There are a limited
    amount of shadow updates per frame available, and the updates are stored
    in a queue. So when displaying many shadow-lights, not each shadowmap is
    update each frame. The reason is, again, performance. When you need a
    custom shadow caster shader, e.g. for alpha blending, you should use the
    Shader/DefaultShaowCaster.* as prefab.

    """

    def __init__(self):
        """ Creates a new pipeline """
        DebugObject.__init__(self, "RenderingPipeline")
        self.showbase = base
        self.settings = None

    def loadSettings(self, filename):
        """ Loads the pipeline settings from an ini file """
        self.settings = PipelineSettingsManager()
        self.settings.loadFromFile(filename)

    def getSettings(self):
        """ Returns the current pipeline settings """
        return self.settings

    def create(self):
        """ Creates this pipeline """

        self.debug("Setting up render pipeline")

        if self.settings is None:
            self.error("You have to call loadSettings first!")
            return

        # Generate auto-configuration for shaders first
        self._generateShaderConfiguration()

        # We use PTA's for shader inputs, because that's faster than
        # using setShaderInput
        self.temporalProjXOffs = PTAInt.emptyArray(1)
        self.cameraPosition = PTAVecBase3f.emptyArray(1)
        self.motionBlurFactor = PTAFloat.emptyArray(1)
        self.lastMVP = PTALMatrix4f.emptyArray(1)
        self.currentMVP = PTALMatrix4f.emptyArray(1)

        self.camera = base.cam
        self.size = self._getSize()
        self.cullBounds = None

        self.showbase.camLens.setNearFar(0.1, 10000)

        # Create light manager, which handles lighting + shadows
        self.lightManager = LightManager(self)

        self.patchSize = LVecBase2i(
            self.settings.computePatchSizeX,
            self.settings.computePatchSizeY)

        # Create separate scene graphs. The deferred graph is render
        self.forwardScene = NodePath("Forward-Rendering")
        self.transparencyScene = NodePath("Transparency-Rendering")

        # We need no transparency (we store other information in the alpha
        # channel)
        render.setAttrib(
            TransparencyAttrib.make(TransparencyAttrib.MNone), 100)

        # Now create deferred render buffers
        self._makeDeferredTargets()

        # Setup the buffers for lighting
        self._createLightingPipeline()

        # Setup combiner for temporal reprojetion
        self._createCombiner()
        self._setupAntialiasing()
        self._setupFinalPass()

        # add update task
        self._attachUpdateTask()

        # display shadow atlas is defined
        if self.settings.displayShadowAtlas:
            self.atlasDisplayImage = OnscreenImage(image=self.lightManager.getAtlasTex(), pos=(
                base.getAspectRatio() - 0.35, 0, 0.5), scale=(0.25, 0, 0.25))

    def getForwardScene(self):
        """ Reparent objects to this scene to use forward rendering.
        Objects in this scene will directly get rendered, with no
        lighting etc. applied. """
        return self.forwardScene

    def getTransparentScene(self):
        """ Reparent objects to this scene to allow this objects to
        have transparency. Objects in this scene will get directly
        rendered and no lighting will get applied. """
        return self.transparencyScene

    def _createCombiner(self):
        """ Creates the target which combines the result from the
        lighting computation and last frame together
        (Temporal Reprojection) """
        self.combiner = RenderTarget("Combine-Temporal")
        self.combiner.addColorTexture()
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
        self.combiner.setShaderInput(
            "temporalProjXOffs", self.temporalProjXOffs)
        self.combiner.setShaderInput("cameraPosition", self.cameraPosition)

        # Set last / current mvp handles
        self.combiner.setShaderInput("lastMVP", self.lastMVP)
        render.setShaderInput("lastMVP", self.lastMVP)
        self.combiner.setShaderInput("currentMVP", self.lastMVP)
        self._setCombinerShader()

    def _setupAntialiasing(self):
        """ Creates the antialiasing technique """

        technique = self.settings.antialiasingTechnique
        self.debug("Creating antialiasing handler for", technique, "..")

        if technique == "SMAA":
            self.antialias = AntialiasingTechniqueSMAA()
        else:
            self.error(
                "Unkown antialiasing technique, using SMAA:", self.antialiasingTechniquel)
            self.antialias = AntialiasingTechniqueSMAA()

        self.antialias.setColorTexture(self.combiner.getColorTexture())
        self.antialias.setDepthTexture(self.deferredTarget.getDepthTexture())
        self.antialias.setup()

        self.antialias.getFirstBuffer().setShaderInput(
            "lastFrame", self.lightingComputeCombinedTex)
        self.antialias.getFirstBuffer().setShaderInput(
            "lastPosition", self.lastPositionBuffer)
        self.antialias.getFirstBuffer().setShaderInput(
            "currentPosition", self.deferredTarget.getColorTexture())

    def _makeDeferredTargets(self):
        """ Creates the multi-render-target """
        self.debug("Creating deferred targets")
        self.deferredTarget = RenderTarget("DeferredTarget")
        self.deferredTarget.addColorAndDepth()
        self.deferredTarget.addAuxTextures(2)
        self.deferredTarget.setAuxBits(16)
        self.deferredTarget.setColorBits(16)
        self.deferredTarget.setDepthBits(32)
        self.deferredTarget.prepareSceneRender()

    def _setupFinalPass(self):
        """ Setups the final pass which applies motion blur and so on """
        colorTex = self.antialias.getResultTexture()
        # Set wrap for motion blur
        colorTex.setWrapU(Texture.WMClamp)
        colorTex.setWrapV(Texture.WMClamp)
        self.deferredTarget.setShaderInput("colorTex", colorTex)
        self.deferredTarget.setShaderInput(
            "velocityTex", self.deferredTarget.getAuxTexture(1))
        self.deferredTarget.setShaderInput(
            "depthTex", self.deferredTarget.getDepthTexture())
        self.deferredTarget.setShaderInput(
            "motionBlurFactor", self.motionBlurFactor)

        self._setFinalPassShader()

    def _makeLightPerTileStorage(self):
        """ Creates a texture to store the lights per tile into. Should
        get replaced with ssbos later """
        storageSizeX = self.precomputeSize.x * 8
        storageSizeY = self.precomputeSize.y * 8

        self.debug(
            "Creating per tile storage of size", storageSizeX, "x", storageSizeY)

        self.lightPerTileStorage = Texture("LightsPerTile")
        self.lightPerTileStorage.setup2dTexture(
            storageSizeX, storageSizeY, Texture.TUnsignedShort, Texture.FR32i)
        self.lightPerTileStorage.setMinfilter(Texture.FTNearest)
        self.lightPerTileStorage.setMagfilter(Texture.FTNearest)

    def _createLightingPipeline(self):
        """ Creates the lighting pipeline, including shadow handling """

        self.debug("Creating lighting pipeline ..")

        # size has to be a multiple of the compute unit size
        # but still has to cover the whole screen
        sizeX = int(math.ceil(self.size.x / self.patchSize.x))
        sizeY = int(math.ceil(self.size.y / self.patchSize.y))

        self.precomputeSize = LVecBase2i(sizeX, sizeY)

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
        self.lightingComputeContainer.setShaderInput(
            "temporalProjXOffs", self.temporalProjXOffs)
        self.lightingComputeContainer.setShaderInput(
            "cameraPosition", self.cameraPosition)

    def _loadFallbackCubemap(self):
        """ Loads the cubemap for image based lighting """
        cubemap = loader.loadCubeMap("Cubemap/#.png")
        cubemap.setMinfilter(Texture.FTLinearMipmapLinear)
        cubemap.setMagfilter(Texture.FTLinearMipmapLinear)
        cubemap.setFormat(Texture.F_srgb_alpha)
        self.lightingComputeContainer.setShaderInput(
            "fallbackCubemap", cubemap)

    def _makeLightBoundsComputationBuffer(self, w, h):
        """ Creates the buffer which precomputes the lights per tile """
        self.debug("Creating light precomputation buffer of size", w, "x", h)
        self.lightBoundsComputeBuff = RenderTarget("ComputeLightTileBounds")
        self.lightBoundsComputeBuff.setSize(w, h)
        self.lightBoundsComputeBuff.setColorWrite(False)
        self.lightBoundsComputeBuff.prepareOffscreenBuffer()

        self.lightBoundsComputeBuff.setShaderInput("mainCam", base.cam)
        self.lightBoundsComputeBuff.setShaderInput("mainRender", base.render)

        self._setPositionComputationShader()

    def _makeLightingComputeBuffer(self):
        """ Creates the buffer which applies the lighting """
        self.lightingComputeContainer = RenderTarget("ComputeLighting")
        self.lightingComputeContainer.setSize(
            base.win.getXSize() / 2,  base.win.getYSize())
        self.lightingComputeContainer.addColorTexture()
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
        """ Sets the shader which applies the light """
        lightShader = BetterShader.load(
            "Shader/DefaultPostProcess.vertex",
            "Shader/ApplyLighting.fragment")
        self.lightingComputeContainer.setShader(lightShader)

    def _setCombinerShader(self):
        """ Sets the shader which combines the lighting with the previous frame
        (temporal reprojection) """
        cShader = BetterShader.load(
            "Shader/DefaultPostProcess.vertex",
            "Shader/Combiner.fragment")
        self.combiner.setShader(cShader)

    def _setPositionComputationShader(self):
        """ Sets the shader which computes the lights per tile """
        pcShader = BetterShader.load(
            "Shader/DefaultPostProcess.vertex",
            "Shader/PrecomputeLights.fragment")
        self.lightBoundsComputeBuff.setShader(pcShader)

    def _setFinalPassShader(self):
        """ Sets the shader which computes the final frame,
        with motion blur and so on """
        fShader = BetterShader.load(
            "Shader/DefaultPostProcess.vertex",
            "Shader/Final.fragment")
        self.deferredTarget.setShader(fShader)

    def _getSize(self):
        """ Returns the window size """
        return Vec2(
            int(self.showbase.win.getXSize()),
            int(self.showbase.win.getYSize()))

    def debugReloadShader(self):
        """ Reloads all shaders """
        self.lightManager.debugReloadShader()
        self._setPositionComputationShader()
        self._setCombinerShader()
        self._setLightingShader()
        self._setFinalPassShader()
        self.antialias.reloadShader()

    def _attachUpdateTask(self):
        """ Attaches the update tasks to the showbase """
        self.showbase.addTask(
            self._update, "UpdateRenderingPipeline", sort=-10000)
        self.showbase.addTask(
            self._updateLights, "UpdateLights", sort=-9000)
        self.showbase.addTask(
            self._updateShadows, "updateShadows", sort=-8000)

    def _computeCameraBounds(self):
        """ Computes the current camera bounds, i.e. for light culling """
        cameraBounds = self.camera.node().getLens().makeBounds()
        cameraBounds.xform(self.camera.getMat(render))
        return cameraBounds

    def _updateLights(self, task=None):
        """ Task which updates/culls the lights """
        self.lightManager.updateLights()
        if task is not None:
            return task.cont

    def _updateShadows(self, task=None):
        """ Task which updates the shadow maps """
        self.lightManager.updateShadows()
        if task is not None:
            return task.cont

    def _update(self, task=None):
        """ Main update task """
        currentFPS = 1.0 / globalClock.getDt()

        self.temporalProjXOffs[0] = 1 - self.temporalProjXOffs[0]
        self.cameraPosition[0] = base.cam.getPos(render)
        self.motionBlurFactor[0] = min(1.5, currentFPS /
                                       60.0) * self.settings.motionBlurFactor

        self.cullBounds = self._computeCameraBounds()
        self.lightManager.setCullBounds(self.cullBounds)

        self.lastMVP[0] = self.currentMVP[0]
        self.currentMVP[0] = self._computeMVP()

        if task is not None:
            return task.cont

    def _computeMVP(self):
        """ Computes the current mvp. Actually, this is the worldViewProjectionMatrix,
        but for convience it's called mvp. """
        projMat = Mat4.convertMat(
            CSYupRight,
            base.camLens.getCoordinateSystem()) * base.camLens.getProjectionMat()
        transformMat = TransformState.makeMat(
            Mat4.convertMat(base.win.getGsg().getInternalCoordinateSystem(),
                            CSZupRight))
        modelViewMat = transformMat.invertCompose(
            render.getTransform(base.cam)).getMat()
        return UnalignedLMatrix4f(modelViewMat * projMat)

    def getLightManager(self):
        """ Returns a handle to the light manager """
        return self.lightManager

    def getDefaultObjectShader(self):
        """ Returns the default shader for objects """
        shader = BetterShader.load(
            "Shader/DefaultObjectShader.vertex", "Shader/DefaultObjectShader.fragment")
        return shader

    def addLight(self, light):
        """ Adds a light to the list of rendered lights """
        self.lightManager.addLight(light)

    def _generateShaderConfiguration(self):
        """ Genrates the global shader include which defines
        most values used in the shaders. """

        # Generate list of defines
        defines = []

        defines.append(
            ("LIGHTING_COMPUTE_PATCH_SIZE_X", self.settings.computePatchSizeX))
        defines.append(
            ("LIGHTING_COMPUTE_PATCH_SIZE_Y", self.settings.computePatchSizeY))
        defines.append(
            ("LIGHTING_MIN_MAX_DEPTH_ACCURACY", self.settings.minMaxDepthAccuracy))

        if self.settings.useSimpleLighting:
            defines.append(("USE_SIMPLE_LIGHTING", 1))

        if self.settings.anyLightBoundCheck:
            defines.append(("LIGHTING_ANY_BOUND_CHECK", 1))

        if self.settings.accurateLightBoundCheck:
            defines.append(("LIGHTING_ACCURATE_BOUND_CHECK", 1))

        if self.settings.renderShadows:
            defines.append(("USE_SHADOWS", 1))

        defines.append(
            ("SHADOW_MAP_ATLAS_SIZE", self.settings.shadowAtlasSize))
        defines.append(
            ("SHADOW_MAX_UPDATES_PER_FRAME", self.settings.maxShadowUpdatesPerFrame))
        defines.append(
            ("SHAODOW_GEOMETRY_MAX_VERTICES", self.settings.maxShadowUpdatesPerFrame * 3))

        defines.append(("SHADOWS_NUM_SAMPLES", self.settings.numShadowSamples))

        if self.settings.useHardwarePCF:
            defines.append(("USE_HARDWARE_PCF", 1))

        defines.append(("WINDOW_WIDTH", base.win.getXSize()))
        defines.append(("WINDOW_HEIGHT", base.win.getYSize()))

        if self.settings.motionBlurEnabled:
            defines.append(("USE_MOTION_BLUR", 1))

        defines.append(("MOTION_BLUR_SAMPLES", self.settings.motionBlurSamples))


        output = "// Autogenerated by RenderPipeline.py\n// Do not edit! Your changes will be lost.\n\n"
        for key, value in defines:
            output += "#define " + key + " " + str(value) + "\n"

        # Try to write the file
        # Todo: add error handling
        handle = open("Shader/Includes/AutoGeneratedConfig.include", "w")
        handle.write(output)
        handle.close()
