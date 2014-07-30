
import math
from os.path import join

from panda3d.core import TransparencyAttrib, Texture, Vec2, NodePath, PTAInt
from panda3d.core import Mat4, CSYupRight, TransformState, CSZupRight
from panda3d.core import PTAFloat, PTALMatrix4f, UnalignedLMatrix4f, LVecBase2i
from panda3d.core import PTAVecBase3f, WindowProperties, OmniBoundingVolume

from direct.gui.OnscreenImage import OnscreenImage

from LightManager import LightManager
from RenderTarget import RenderTarget
from DebugObject import DebugObject
from BetterShader import BetterShader
from Antialiasing import *
from AmbientOcclusion import *
from PipelineSettingsManager import PipelineSettingsManager
from PipelineGuiManager import PipelineGuiManager
from Globals import Globals


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

    def __init__(self, showbase):
        """ Creates a new pipeline """
        DebugObject.__init__(self, "RenderingPipeline")
        self.showbase = showbase
        self.settings = None
        self.rootDirectory = "../RenderPipeline/"

    def loadSettings(self, filename):
        """ Loads the pipeline settings from an ini file """
        self.settings = PipelineSettingsManager()
        self.settings.loadFromFile(filename)

    def setRootDirectory(self, directory):
        """ Sets the root directory of this pipeline, all assets
        will be loaded relative to this directory """
        self.rootDirectory = directory.replace("\\", "/").rstrip("/")

    def getSettings(self):
        """ Returns the current pipeline settings """
        return self.settings

    def create(self):
        """ Creates this pipeline """

        self.debug("Setting up render pipeline")
        self.debug("Root directory is '" + self.rootDirectory + "'")

        if self.settings is None:
            self.error("You have to call loadSettings first!")
            return

        # Store globals, as cython can't handle them
        self.debug("Setting up globals")
        Globals.load(self.showbase, self.rootDirectory)

        # We use PTA's for shader inputs, because that's faster than
        # using setShaderInput
        self.temporalProjXOffs = PTAInt.emptyArray(1)
        self.cameraPosition = PTAVecBase3f.emptyArray(1)
        self.motionBlurFactor = PTAFloat.emptyArray(1)
        self.lastMVP = PTALMatrix4f.emptyArray(1)
        self.currentMVP = PTALMatrix4f.emptyArray(1)

        # Create onscreen gui

        # For the temporal reprojection it is important that the window width is
        # a multiple of 2
        if self.showbase.win.getXSize() % 2 == 1:
            self.error(
                "The window has to have a width which is a multiple of 2 (Current: ", self.showbase.win.getXSize(), ")")
            self.error(
                "I'll correct that for you, but next time pass the correct window size!")

            wp = WindowProperties()
            wp.setSize(
                self.showbase.win.getXSize() + 1, self.showbase.win.getYSize())
            self.showbase.win.requestProperties(wp)
            self.showbase.graphicsEngine.openWindows()

        self.camera = self.showbase.cam
        self.size = self._getSize()
        self.cullBounds = None

        # Debug variables to disable specific features
        self.haveLightingPass = True

        # haveCombiner can only be true when haveLightingPass is enabled
        self.haveCombiner = True
        self.haveMRT = True

        # Not as good as I want it, so disabled. I'll work on it.
        self.blurEnabled = False

        self.debug("Window size is", self.size.x, "x", self.size.y)

        self.showbase.camLens.setNearFar(0.1, 30000)
        self.showbase.camLens.setFov(90)

        self._setupOcclusion()

        # Create light manager, which handles lighting + shadows
        if self.haveLightingPass:
            self.lightManager = LightManager(self)

        self.patchSize = LVecBase2i(
            self.settings.computePatchSizeX,
            self.settings.computePatchSizeY)

        # Create separate scene graphs. The deferred graph is render
        self.forwardScene = NodePath("Forward-Rendering")
        self.transparencyScene = NodePath("Transparency-Rendering")

        # We need no transparency (we store other information in the alpha
        # channel)
        self.showbase.render.setAttrib(
            TransparencyAttrib.make(TransparencyAttrib.MNone), 100)

        # Now create deferred render buffers
        self._makeDeferredTargets()

        # Create the target which constructs the view-space normals and
        # position from world-space position
        if self.occlusion.requiresViewSpacePosNrm():
            self._createNormalPrecomputeBuffer()

        # Setup the buffers for lighting
        self._createLightingPipeline()

        # Setup combiner for temporal reprojetion
        if self.haveCombiner:
            self._createCombiner()

        if self.occlusion.requiresBlurring():
            self._createOcclusionBlurBuffer()

        self._setupAntialiasing()

        if self.blurEnabled:
            self._createDofStorage()
            self._createBlurBuffer()

        self._setupFinalPass()
        self._setShaderInputs()

        # add update task
        self._attachUpdateTask()

        if self.settings.displayOnscreenDebugger:
            self.guiManager = PipelineGuiManager(self)
            self.guiManager.setup()

        # Generate auto-configuration for shaders
        self._generateShaderConfiguration()

        # display shadow atlas is defined
        # todo: move this to the gui manager
        # if self.settings.displayShadowAtlas and self.haveLightingPass:
        # self.atlasDisplayImage = OnscreenImage(
        #     image=self.lightManager.getAtlasTex(), pos=(
        #         self.showbase.getAspectRatio() - 0.55, 0, 0.2),
        #     scale=(0.5, 0, 0.5))

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
        self.combiner.setColorBits(16)
        self.combiner.prepareOffscreenBuffer()
        self._setCombinerShader()

    def _setupAntialiasing(self):
        """ Creates the antialiasing technique """
        technique = self.settings.antialiasingTechnique
        self.debug("Creating antialiasing handler for", technique)

        if technique == "None":
            self.antialias = AntialiasingTechniqueNone()
        elif technique == "SMAA":
            self.antialias = AntialiasingTechniqueSMAA()
        else:
            self.error(
                "Unkown antialiasing technique", technique, "-> using None:")
            self.antialias = AntialiasingTechniqueNone()

        if self.occlusion.requiresBlurring():
            self.antialias.setColorTexture(
                self.blurOcclusionH.getColorTexture())
        else:
            if self.haveCombiner:
                self.antialias.setColorTexture(self.combiner.getColorTexture())
            else:
                self.antialias.setColorTexture(
                    self.deferredTarget.getColorTexture())

        self.antialias.setDepthTexture(self.deferredTarget.getDepthTexture())
        self.antialias.setup()

    def _setupOcclusion(self):
        """ Creates the occlusion technique """
        technique = self.settings.occlusionTechnique
        self.debug("Creating occlusion handle for", technique)

        if technique == "None":
            self.occlusion = AmbientOcclusionTechniqueNone()
        elif technique == "SAO":
            self.occlusion = AmbientOcclusionTechniqueSAO()
        else:
            self.error("Unkown occlusion technique:", technique)
            self.occlusion = AmbientOcclusionTechniqueNone()

    def _makeDeferredTargets(self):
        """ Creates the multi-render-target """
        self.debug("Creating deferred targets")
        self.deferredTarget = RenderTarget("DeferredTarget")
        self.deferredTarget.addColorAndDepth()

        if self.haveMRT:
            self.deferredTarget.addAuxTextures(3)
            self.deferredTarget.setAuxBits(16)
            self.deferredTarget.setColorBits(16)
            self.deferredTarget.setDepthBits(32)

        # GL_INVALID_OPERATION ?
        # self.deferredTarget.setMultisamples(1)

        self.deferredTarget.prepareSceneRender()

    def _setupFinalPass(self):
        """ Setups the final pass which applies motion blur and so on """
        # Set wrap for motion blur
        colorTex = self.antialias.getResultTexture()
        colorTex.setWrapU(Texture.WMClamp)
        colorTex.setWrapV(Texture.WMClamp)
        self._setFinalPassShader()

    def _makeLightPerTileStorage(self):
        """ Creates a texture to store the lights per tile into. Should
        get replaced with ssbos later """
        storageSizeX = self.precomputeSize.x * 8
        storageSizeY = self.precomputeSize.y * 8

        self.debug(
            "Creating per tile storage of size",
            storageSizeX, "x", storageSizeY)

        self.lightPerTileStorage = Texture("LightsPerTile")
        self.lightPerTileStorage.setup2dTexture(
            storageSizeX, storageSizeY, Texture.TUnsignedShort, Texture.FR32i)
        self.lightPerTileStorage.setMinfilter(Texture.FTNearest)
        self.lightPerTileStorage.setMagfilter(Texture.FTNearest)

    def _createLightingPipeline(self):
        """ Creates the lighting pipeline, including shadow handling """

        if not self.haveLightingPass:
            self.debug("Skipping lighting pipeline")
            return

        self.debug("Creating lighting pipeline ..")

        # size has to be a multiple of the compute unit size
        # but still has to cover the whole screen
        sizeX = int(math.ceil(float(self.size.x) / self.patchSize.x))
        sizeY = int(math.ceil(float(self.size.y) / self.patchSize.y))

        self.precomputeSize = LVecBase2i(sizeX, sizeY)

        self.debug("Batch size =", sizeX, "x", sizeY,
                   "Actual Buffer size=", int(sizeX * self.patchSize.x),
                   "x", int(sizeY * self.patchSize.y))

        self._makeLightPerTileStorage()

        # Create a buffer which computes which light affects which tile
        self._makeLightBoundsComputationBuffer(sizeX, sizeY)

        # Create a buffer which applies the lighting
        self._makeLightingComputeBuffer()

        # Register for light manager
        self.lightManager.setLightingComputator(self.lightingComputeContainer)
        self.lightManager.setLightingCuller(self.lightBoundsComputeBuff)

        self._loadFallbackCubemap()
        self._loadLookupCubemap()

    def _setShaderInputs(self):
        """ Sets most of the required shader inputs to the targets """

        # Shader inputs for the light-culling pass
        if self.haveLightingPass:
            self.lightBoundsComputeBuff.setShaderInput(
                "destination", self.lightPerTileStorage)
            self.lightBoundsComputeBuff.setShaderInput(
                "depth", self.deferredTarget.getDepthTexture())
            self.lightBoundsComputeBuff.setShaderInput(
                "mainCam", self.showbase.cam)
            self.lightBoundsComputeBuff.setShaderInput(
                "mainRender", self.showbase.render)

            # Shader inputs for the light-applying pass
            self.lightingComputeContainer.setShaderInput(
                "data0", self.deferredTarget.getColorTexture())
            self.lightingComputeContainer.setShaderInput(
                "data1", self.deferredTarget.getAuxTexture(0))
            self.lightingComputeContainer.setShaderInput(
                "data2", self.deferredTarget.getAuxTexture(1))
            self.lightingComputeContainer.setShaderInput(
                "data3", self.deferredTarget.getAuxTexture(2))
            self.lightingComputeContainer.setShaderInput(
                "depth", self.deferredTarget.getDepthTexture())

            if self.occlusion.requiresViewSpacePosNrm():
                self.lightingComputeContainer.setShaderInput(
                    "viewSpaceNormals", self.normalPrecompute.getColorTexture())
                self.lightingComputeContainer.setShaderInput(
                    "viewSpacePosition", self.normalPrecompute.getAuxTexture(0))

            self.lightingComputeContainer.setShaderInput(
                "shadowAtlas", self.lightManager.getAtlasTex())
            self.lightingComputeContainer.setShaderInput(
                "destination", self.lightingComputeCombinedTex)
            self.lightingComputeContainer.setShaderInput(
                "temporalProjXOffs", self.temporalProjXOffs)
            self.lightingComputeContainer.setShaderInput(
                "cameraPosition", self.cameraPosition)

            self.lightingComputeContainer.setShaderInput(
                "noiseTexture", self.showbase.loader.loadTexture("Data/Occlusion/noise4x4.png"))
            self.lightingComputeContainer.setShaderInput(
                "lightsPerTile", self.lightPerTileStorage)

        # Shader inputs for the occlusion blur passes
        if self.occlusion.requiresBlurring() and self.haveCombiner:
            self.blurOcclusionH.setShaderInput(
                "colorTex", self.blurOcclusionV.getColorTexture())
            self.blurOcclusionV.setShaderInput(
                "colorTex", self.combiner.getColorTexture())
            self.blurOcclusionH.setShaderInput(
                "normalTex", self.deferredTarget.getAuxTexture(0))
            self.blurOcclusionV.setShaderInput(
                "normalTex", self.deferredTarget.getAuxTexture(0))
            self.blurOcclusionH.setShaderInput(
                "normalsView", self.normalPrecompute.getAuxTexture(0))
            self.blurOcclusionV.setShaderInput(
                "normalsView", self.normalPrecompute.getAuxTexture(0))

        # Shader inputs for the blur passes
        if self.blurEnabled:
            self.blurColorH.setShaderInput(
                "dofStorage", self.dofStorage)
            self.blurColorV.setShaderInput(
                "dofStorage", self.dofStorage)
            self.blurColorH.setShaderInput("colorTex",
                                           self.antialias.getResultTexture())
            self.blurColorH.setShaderInput("depthTex",
                                           self.deferredTarget.getDepthTexture())
            self.blurColorV.setShaderInput("colorTex",
                                           self.blurColorH.getColorTexture())

        # Shader inputs for the temporal reprojection
        if self.haveCombiner:
            self.combiner.setShaderInput(
                "currentComputation",
                self.lightingComputeContainer.getColorTexture())
            self.combiner.setShaderInput(
                "lastFrame", self.lightingComputeCombinedTex)
            self.combiner.setShaderInput(
                "positionBuffer", self.deferredTarget.getColorTexture())
            self.combiner.setShaderInput(
                "velocityBuffer", self.deferredTarget.getAuxTexture(1))

            if self.blurEnabled:
                self.combiner.setShaderInput(
                    "dofStorage", self.dofStorage)

            self.combiner.setShaderInput(
                "depthTex", self.deferredTarget.getDepthTexture())
            self.combiner.setShaderInput(
                "lastPosition", self.lastPositionBuffer)
            self.combiner.setShaderInput(
                "temporalProjXOffs", self.temporalProjXOffs)
            self.combiner.setShaderInput("lastMVP", self.lastMVP)
            self.combiner.setShaderInput("cameraPosition", self.cameraPosition)
            self.combiner.setShaderInput("currentMVP", self.lastMVP)

        # Shader inputs for the final pass
        if self.blurEnabled:
            self.deferredTarget.setShaderInput(
                "colorTex", self.blurColorV.getColorTexture())
        else:
            self.deferredTarget.setShaderInput(
                "colorTex", self.antialias.getResultTexture())

        if self.occlusion.requiresBlurring():
            self.normalPrecompute.setShaderInput(
                "positionTex", self.deferredTarget.getColorTexture())
            self.normalPrecompute.setShaderInput(
                "mainCam", self.showbase.cam)
            self.normalPrecompute.setShaderInput(
                "mainRender", self.showbase.render)
            self.normalPrecompute.setShaderInput(
                "depthTex", self.deferredTarget.getDepthTexture())

        if self.haveMRT:
            self.deferredTarget.setShaderInput(
                "velocityTex", self.deferredTarget.getAuxTexture(1))

        self.deferredTarget.setShaderInput(
            "depthTex", self.deferredTarget.getDepthTexture())
        self.deferredTarget.setShaderInput(
            "motionBlurFactor", self.motionBlurFactor)

        if self.haveLightingPass:
            self.deferredTarget.setShaderInput(
                "lastFrame", self.lightingComputeCombinedTex)

        if self.haveCombiner:
            self.deferredTarget.setShaderInput(
                "newFrame", self.combiner.getColorTexture())
            self.deferredTarget.setShaderInput(
                "lastPosition", self.lastPositionBuffer)

        self.deferredTarget.setShaderInput(
            "currentPosition", self.deferredTarget.getColorTexture())

        # Set last / current mvp handles
        self.showbase.render.setShaderInput("lastMVP", self.lastMVP)

        # Finally, set shaders
        self.reloadShaders()

    def _loadFallbackCubemap(self):
        """ Loads the cubemap for image based lighting """
        cubemap = self.showbase.loader.loadCubeMap(
            join(self.rootDirectory, "Data/Cubemaps/Default/#.png"))
        cubemap.setMinfilter(Texture.FTLinearMipmapLinear)
        cubemap.setMagfilter(Texture.FTLinearMipmapLinear)
        cubemap.setFormat(Texture.F_srgb_alpha)
        self.lightingComputeContainer.setShaderInput(
            "fallbackCubemap", cubemap)

    def _loadLookupCubemap(self):
        self.debug("Loading lookup cubemap")
        cubemap = self.showbase.loader.loadCubeMap(
            join(self.rootDirectory, "Data/Cubemaps/DirectionLookup/#.png"))
        cubemap.setMinfilter(Texture.FTNearest)
        cubemap.setMagfilter(Texture.FTNearest)
        cubemap.setFormat(Texture.F_rgb8)
        self.lightingComputeContainer.setShaderInput(
            "directionToFace", cubemap)

    def _makeLightBoundsComputationBuffer(self, w, h):
        """ Creates the buffer which precomputes the lights per tile """
        self.debug("Creating light precomputation buffer of size", w, "x", h)
        self.lightBoundsComputeBuff = RenderTarget("ComputeLightTileBounds")
        self.lightBoundsComputeBuff.setSize(w, h)
        self.lightBoundsComputeBuff.setColorWrite(False)
        self.lightBoundsComputeBuff.prepareOffscreenBuffer()

    def _makeLightingComputeBuffer(self):
        """ Creates the buffer which applies the lighting """
        self.lightingComputeContainer = RenderTarget("ComputeLighting")
        self.lightingComputeContainer.setSize(
            self.showbase.win.getXSize() / 2,  self.showbase.win.getYSize())
        self.lightingComputeContainer.addColorTexture()
        self.lightingComputeContainer.setColorBits(16)
        self.lightingComputeContainer.prepareOffscreenBuffer()

        self.lightingComputeCombinedTex = Texture("Lighting-Compute-Combined")
        self.lightingComputeCombinedTex.setup2dTexture(
            self.showbase.win.getXSize(), self.showbase.win.getYSize(),
            Texture.TFloat, Texture.FRgba8)
        self.lightingComputeCombinedTex.setMinfilter(Texture.FTLinear)
        self.lightingComputeCombinedTex.setMagfilter(Texture.FTLinear)

        self.lastPositionBuffer = Texture("Last-Position-Buffer")
        self.lastPositionBuffer.setup2dTexture(
            self.showbase.win.getXSize(), self.showbase.win.getYSize(),
            Texture.TFloat, Texture.FRgba16)
        self.lastPositionBuffer.setMinfilter(Texture.FTNearest)
        self.lastPositionBuffer.setMagfilter(Texture.FTNearest)

    def _createOcclusionBlurBuffer(self):
        """ Creates the buffers needed to blur the occlusion """
        self.blurOcclusionV = RenderTarget("blurOcclusionVertical")
        self.blurOcclusionV.addColorTexture()
        self.blurOcclusionV.prepareOffscreenBuffer()

        self.blurOcclusionH = RenderTarget("blurOcclusionHorizontal")
        self.blurOcclusionH.addColorTexture()
        self.blurOcclusionH.prepareOffscreenBuffer()

        # Mipmaps for blur?
        # self.blurOcclusionV.getColorTexture().setMinfilter(
        #     Texture.FTLinearMipmapLinear)
        # self.combiner.getColorTexture().setMinfilter(
        #     Texture.FTLinearMipmapLinear)

    def _createBlurBuffer(self):
        """ Creates the buffers for the dof """
        self.blurColorV = RenderTarget("blurColorVertical")
        self.blurColorV.addColorTexture()
        self.blurColorV.prepareOffscreenBuffer()

        self.blurColorH = RenderTarget("blurColorHorizontal")
        self.blurColorH.addColorTexture()
        self.blurColorH.prepareOffscreenBuffer()

        # self.blurColorH.getColorTexture().setMinfilter(
        #     Texture.FTLinearMipmapLinear)
        # self.antialias.getResultTexture().setMinfilter(
        #     Texture.FTLinearMipmapLinear)

    def _createNormalPrecomputeBuffer(self):
        """ Creates a buffer which reconstructs the normals and position
        from view-space """
        self.normalPrecompute = RenderTarget("PrecomputeNormals")
        self.normalPrecompute.addColorTexture()
        self.normalPrecompute.addAuxTextures(1)
        self.normalPrecompute.setColorBits(16)
        self.normalPrecompute.setAuxBits(16)
        self.normalPrecompute.prepareOffscreenBuffer()

    def _createDofStorage(self):
        """ Creates the texture where the dof factor is stored in, so we
        don't recompute it each pass """
        self.dofStorage = Texture("DOFStorage")
        self.dofStorage.setup2dTexture(
            self.showbase.win.getXSize(), self.showbase.win.getYSize(),
            Texture.TFloat, Texture.FRg16)

    def _setOcclusionBlurShader(self):
        """ Sets the shaders which blur the occlusion """
        blurVShader = BetterShader.load(
            "Shader/DefaultPostProcess.vertex",
            "Shader/BlurOcclusionVertical.fragment")
        blurHShader = BetterShader.load(
            "Shader/DefaultPostProcess.vertex",
            "Shader/BlurOcclusionHorizontal.fragment")
        self.blurOcclusionV.setShader(blurVShader)
        self.blurOcclusionH.setShader(blurHShader)

    def _setBlurShader(self):
        """ Sets the shaders which blur the color """
        blurVShader = BetterShader.load(
            "Shader/DefaultPostProcess.vertex",
            "Shader/BlurVertical.fragment")
        blurHShader = BetterShader.load(
            "Shader/DefaultPostProcess.vertex",
            "Shader/BlurHorizontal.fragment")
        self.blurColorV.setShader(blurVShader)
        self.blurColorH.setShader(blurHShader)

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
        """ Returns the window size. """
        return LVecBase2i(
            self.showbase.win.getXSize(),
            self.showbase.win.getYSize())

    def reloadShaders(self):
        """ Reloads all shaders """

        if self.haveLightingPass:
            self.lightManager.debugReloadShader()
            self._setPositionComputationShader()
            self._setLightingShader()

        if self.haveCombiner:
            self._setCombinerShader()

        self._setFinalPassShader()

        if self.occlusion.requiresBlurring():
            self._setOcclusionBlurShader()

        if self.blurEnabled:
            self._setBlurShader()

        if self.occlusion.requiresViewSpacePosNrm():
            self._setNormalExtractShader()

        self.antialias.reloadShader()

    def _setNormalExtractShader(self):
        """ Sets the shader which constructs the normals from position """
        npShader = BetterShader.load(
            "Shader/DefaultPostProcess.vertex",
            "Shader/ExtractNormals.fragment")
        self.normalPrecompute.setShader(npShader)

    def _attachUpdateTask(self):
        """ Attaches the update tasks to the showbase """

        self.showbase.addTask(
            self._update, "UpdateRenderingPipeline", sort=-10000)

        if self.haveLightingPass:
            self.showbase.addTask(
                self._updateLights, "UpdateLights", sort=-9000)
            self.showbase.addTask(
                self._updateShadows, "updateShadows", sort=-8000)

        if self.settings.displayOnscreenDebugger:
            self.showbase.addTask(
                self._updateGUI, "UpdateGUI", sort=7000)

    def _computeCameraBounds(self):
        """ Computes the current camera bounds, i.e. for light culling """
        cameraBounds = self.camera.node().getLens().makeBounds()
        cameraBounds.xform(self.camera.getMat(self.showbase.render))
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

    def _updateGUI(self, task=None):
        """ Task which updates the onscreen gui debugger """
        self.guiManager.update()

        if task is not None:
            return task.cont

    def _update(self, task=None):
        """ Main update task """
        currentFPS = 1.0 / self.showbase.taskMgr.globalClock.getDt()

        self.temporalProjXOffs[0] = 1 - self.temporalProjXOffs[0]
        self.cameraPosition[0] = self.showbase.cam.getPos(self.showbase.render)
        self.motionBlurFactor[0] = min(1.5, currentFPS /
                                       60.0) * self.settings.motionBlurFactor

        self.cullBounds = self._computeCameraBounds()

        if self.haveLightingPass:
            self.lightManager.setCullBounds(self.cullBounds)

        self.lastMVP[0] = self.currentMVP[0]
        self.currentMVP[0] = self._computeMVP()

        if task is not None:
            return task.cont

    def _computeMVP(self):
        """ Computes the current mvp. Actually, this is the
        worldViewProjectionMatrix, but for convience it's called mvp. """
        camLens = self.showbase.camLens
        projMat = Mat4.convertMat(
            CSYupRight,
            camLens.getCoordinateSystem()) * camLens.getProjectionMat()
        transformMat = TransformState.makeMat(
            Mat4.convertMat(self.showbase.win.getGsg().getInternalCoordinateSystem(),
                            CSZupRight))
        modelViewMat = transformMat.invertCompose(
            self.showbase.render.getTransform(self.showbase.cam)).getMat()
        return UnalignedLMatrix4f(modelViewMat * projMat)

    def getLightManager(self):
        """ Returns a handle to the light manager """
        return self.lightManager

    def getDefaultObjectShader(self, tesselated=False):
        """ Returns the default shader for objects """

        if not tesselated:
            shader = BetterShader.load(
                "Shader/DefaultObjectShader/vertex.glsl",
                "Shader/DefaultObjectShader/fragment.glsl")
        else:
            self.warn(
                "Tesselation is only experimental! Remember "
                "to convert the geometry to patches first!")

            shader = BetterShader.load(
                "Shader/DefaultObjectShader/vertex.glsl",
                "Shader/DefaultObjectShader/fragment.glsl",
                "",
                "Shader/DefaultObjectShader/tesscontrol.glsl",
                "Shader/DefaultObjectShader/tesseval.glsl")

        return shader

    def addLight(self, light):
        """ Adds a light to the list of rendered lights """
        if self.haveLightingPass:
            self.lightManager.addLight(light)
        else:
            self.warn("Lighting is disabled, so addLight has no effect")

    def _generateShaderConfiguration(self):
        """ Genrates the global shader include which defines
        most values used in the shaders. """

        self.debug("(Re)Generating shader configuration")

        # Generate list of defines
        defines = []

        if self.settings.antialiasingTechnique == "SMAA":
            quality = self.settings.smaaQuality.upper()
            if quality in ["LOW", "MEDIUM", "HIGH", "ULTRA"]:
                defines.append(("SMAA_PRESET_" + quality, ""))
            else:
                self.error("Unrecognized SMAA quality:", quality)
                return

        defines.append(
            ("LIGHTING_COMPUTE_PATCH_SIZE_X", self.settings.computePatchSizeX))
        defines.append(
            ("LIGHTING_COMPUTE_PATCH_SIZE_Y", self.settings.computePatchSizeY))
        defines.append(
            ("LIGHTING_MIN_MAX_DEPTH_ACCURACY", self.settings.minMaxDepthAccuracy))

        if self.blurEnabled:
            defines.append(("USE_DOF", 1))

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

        defines.append(("WINDOW_WIDTH", self.showbase.win.getXSize()))
        defines.append(("WINDOW_HEIGHT", self.showbase.win.getYSize()))

        if self.settings.motionBlurEnabled:
            defines.append(("USE_MOTION_BLUR", 1))

        defines.append(
            ("MOTION_BLUR_SAMPLES", self.settings.motionBlurSamples))

        # Occlusion
        defines.append(
            ("OCCLUSION_TECHNIQUE_" + self.occlusion.getIncludeName(), 1))
        defines.append(
            ("OCCLUSION_RADIUS", self.settings.occlusionRadius))
        defines.append(
            ("OCCLUSION_STRENGTH", self.settings.occlusionStrength))
        defines.append(
            ("OCCLUSION_SAMPLES", self.settings.occlusionSampleCount))

        if self.settings.displayOnscreenDebugger:
            defines.append(("DEBUGGER_ACTIVE", 1))

            extraSettings = self.guiManager.getDefines()
            defines += extraSettings

        # Additional gui settings
        output = "// Autogenerated by RenderingPipeline.py\n"
        output += "// Do not edit! Your changes will be lost.\n\n"

        for key, value in defines:
            output += "#define " + key + " " + str(value) + "\n"

        # Try to write the file
        # Todo: add error handling
        handle = open(
            join(Globals.rootDirectory, "Shader/Includes/AutoGeneratedConfig.include"), "w")
        handle.write(output)
        handle.close()

    def onWindowResized(self):
        """ Call this whenever the window resized """
        raise NotImplementedError()

    def destroy(self):
        """ Call this when you want to shut down the pipeline """
        raise NotImplementedError()

    def reload(self):
        """ This reloads the whole pipeline, same as destroy(); create() """
        self.debug("Reloading pipeline")
        self.destroy()
        self.create()

    def setActive(self, active):
        """ You can enable/disable the pipeline, for example
        when the user is in the menu, the 3d scene does not have
        to be rendered """
        raise NotImplementedError()
