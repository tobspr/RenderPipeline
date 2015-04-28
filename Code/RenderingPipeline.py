
import math
import os
import random

from panda3d.core import TransparencyAttrib, Texture, NodePath, PTAInt, Vec3
from panda3d.core import Mat4, CSYupRight, TransformState, CSZupRight
from panda3d.core import PTAFloat, PTALMatrix4f, UnalignedLMatrix4f, LVecBase2i
from panda3d.core import PTAVecBase3f, WindowProperties, Vec4, Vec2, PTAVecBase2f
from panda3d.core import SamplerState
from panda3d.core import Shader

from direct.stdpy.file import open

from LightManager import LightManager
from RenderTarget import RenderTarget
from DebugObject import DebugObject
from BetterShader import BetterShader
from GlobalIllumination import GlobalIllumination
from Antialiasing import *
from AmbientOcclusion import *
from PipelineSettingsManager import PipelineSettingsManager
from GUI.PipelineGuiManager import PipelineGuiManager
from Globals import Globals
from SystemAnalyzer import SystemAnalyzer
from MountManager import MountManager
from Scattering import Scattering

from GUI.BufferViewerGUI import BufferViewerGUI


class RenderingPipeline(DebugObject):

    """ This is the core class, driving all other classes. To use this
    pipeline, your code has to call this *after* the initialization of ShowBase:

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
        self.mountManager = MountManager()

    def getMountManager(self):
        """ Returns the mount manager. You can use this to set the
        write directory and base path """
        return self.mountManager

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

        self.debug("Analyzing system ..")
        SystemAnalyzer.analyze()


        self.debug("Checking required Panda3D version ..")
        #SystemAnalyzer.checkPandaVersionOutOfDate(01,12,2014)

        # Mount everything first
        self.mountManager.mount()

        # Store globals, as cython can't handle them
        self.debug("Setting up globals")
        Globals.load(self.showbase)
        Globals.font = loader.loadFont("Data/Font/SourceSansPro-Semibold.otf")
        Globals.font.setPixelsPerUnit(25)

        # Setting up shader loading
        BetterShader._DumpShaders = self.settings.dumpGeneratedShaders

        # We use PTA's for shader inputs, because that's faster than
        # using setShaderInput
        self.cameraPosition = PTAVecBase3f.emptyArray(1)
        self.motionBlurFactor = PTAFloat.emptyArray(1)
        self.lastMVP = PTALMatrix4f.emptyArray(1)
        self.currentMVP = PTALMatrix4f.emptyArray(1)
        self.currentShiftIndex = PTAInt.emptyArray(1)
        self.frameIndex = PTAInt.emptyArray(1)

        # Initialize variables
        self.camera = self.showbase.cam
        self.size = self._getSize()
        self.cullBounds = None


        # It is important that the window width is a multiple of 2
        if self.size.x % 2 == 1:
            self.error(
                "The window has to have a width which is a multiple of 2 "
                "(Current: ", self.showbase.win.getXSize(), ")")
            self.error(
                "I'll correct that for you, but next time pass the correct "
                "window size!")

            wp = WindowProperties()
            wp.setSize(
                self.showbase.win.getXSize() + 1, self.showbase.win.getYSize())
            self.showbase.win.requestProperties(wp)
            self.showbase.graphicsEngine.openWindows()

            # Get new size
            self.size = self._getSize()

        # Debug variables to disable specific features
        self.haveLightingPass = True
        self.haveMRT = True
        self.haveOcclusion = False


        # Not as good as I want it, so disabled. I'll work on it.
        self.blurEnabled = False

        self.debug("Window size is", self.size.x, "x", self.size.y)

        self.showbase.camLens.setNearFar(0.1, 50000)
        self.showbase.camLens.setFov(90)

        self.showbase.win.setClearColor(Vec4(1.0, 0.0, 1.0, 1.0))

        # Create occlusion handler
        self._setupOcclusion()

        # Create GI handler
        if self.settings.enableGlobalIllumination:
            self.globalIllum = GlobalIllumination(self)


        # We need last frame position for occlusion and gi
        if self.haveOcclusion or self.settings.enableGlobalIllumination:
            self._setupLastFrameTextures()


        if self.settings.displayOnscreenDebugger:
            self.guiManager = PipelineGuiManager(self)
            self.guiManager.setup()

        # Generate auto-configuration for shaders
        self._generateShaderConfiguration()

        # Setup GI
        if self.settings.enableGlobalIllumination:
            self._setupGlobalIllumination()

        # Create light manager, which handles lighting + shadows
        if self.haveLightingPass:
            self.lightManager = LightManager(self)

        self.patchSize = LVecBase2i(
            self.settings.computePatchSizeX,
            self.settings.computePatchSizeY)

        # Create separate scene graphs. The standard deferred graph is stored 
        # in base.render
        self.forwardScene = NodePath("Forward-Rendering")
        self.transparencyScene = NodePath("Transparency-Rendering")
        self.transparencyScene.setBin("transparent", 30)

        # We need no transparency (we store different information in the alpha
        # channel)
        self.showbase.render.setAttrib(
            TransparencyAttrib.make(TransparencyAttrib.MNone), 100)

        # Now create deferred render buffers
        self._makeDeferredTargets()

        # Create the target which constructs the view-space normals and
        # position from world-space position
        if self.occlusion.requiresViewSpacePosNrm():
            self._createNormalPrecomputeBuffer()

        if self.settings.enableGlobalIllumination:
            self._creatGIPrecomputeBuffer()


        # Create occlusion buffer
        if self.occlusion.hasSeparatePass():
            self._setupOcclusionBuffer()


        # Setup the buffers for lighting
        self._createLightingPipeline()

        if self.occlusion.requiresBlurring():
            self._createOcclusionBlurBuffer()

        self._setupAntialiasing()

        if self.blurEnabled:
            self._createDofStorage()
            self._createBlurBuffer()

        # Not sure why it has to be that value. But that leads to the best result
        aspect = float(self.size.y) / self.size.x
        self.onePixelShift = Vec2(
            0.125 / self.size.x, 0.125 / self.size.y) * self.settings.jitterAmount

        # Annoying that Vec2 has no multliply-operator for non-floats
        multiplyVec2 = lambda a, b: Vec2(a.x*b.x, a.y*b.y)

        if self.antialias.requiresJittering():
            self.pixelShifts = [
                multiplyVec2(self.onePixelShift, Vec2(-0.25,  0.25)),
                multiplyVec2(self.onePixelShift, Vec2(0.25, -0.25))
            ]
        else:
            self.pixelShifts = [Vec2(0), Vec2(0)]
        self.currentPixelShift = PTAVecBase2f.emptyArray(1)
        self.lastPixelShift = PTAVecBase2f.emptyArray(1)

        self._setupFinalPass()
        self._setShaderInputs()

        # Give the gui a hint when the pipeline is done loading
        if self.settings.displayOnscreenDebugger:
            self.guiManager.onPipelineLoaded()

        # add update task
        self._attachUpdateTask()

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

    def _setupGlobalIllumination(self):
        """ Creates the GI handler """
        #self.globalIllum = GlobalIllumination(self)
        self.globalIllum.setup()

    def _setupAntialiasing(self):
        """ Creates the antialiasing technique """
        technique = self.settings.antialiasingTechnique
        self.debug("Creating antialiasing handler for", technique)

        if technique == "None":
            self.antialias = AntialiasingTechniqueNone()
        elif technique == "SMAA":
            self.antialias = AntialiasingTechniqueSMAA()
        elif technique == "FXAA":
            self.antialias = AntialiasingTechniqueFXAA()
        else:
            self.error(
                "Unkown antialiasing technique", technique, "-> using None:")
            self.antialias = AntialiasingTechniqueNone()

        if self.occlusion.requiresBlurring():
            self.antialias.setColorTexture(
                self.blurOcclusionH.getColorTexture())
        else:
            self.antialias.setColorTexture(
                self.lightingComputeContainer.getColorTexture())

        self.antialias.setDepthTexture(self.deferredTarget.getDepthTexture())
        self.antialias.setVelocityTexture(self.deferredTarget.getAuxTexture(1))
        self.antialias.setup()

    def _setupOcclusion(self):
        """ Creates the occlusion technique """
        technique = self.settings.occlusionTechnique
        self.debug("Creating occlusion handle for", technique)

        if technique == "None":
            self.occlusion = AmbientOcclusionTechniqueNone()
        elif technique == "SAO":
            self.occlusion = AmbientOcclusionTechniqueSAO() 
            self.haveOcclusion = True
        elif technique == "HBAO":
            self.occlusion = AmbientOcclusionTechniqueHBAO() 
            self.haveOcclusion = True
        else:
            self.error("Unkown occlusion technique:", technique)
            self.occlusion = AmbientOcclusionTechniqueNone()

    def _setupOcclusionBuffer(self):
        """ Creates a buffer at half resolution for the occlusion """
        self.occlusionBuffer = RenderTarget("OcclusionCompute")
        self.occlusionBuffer.setSize(self.size.x / 2, self.size.y / 2)
        self.occlusionBuffer.addColorTexture()
        self.occlusionBuffer.prepareOffscreenBuffer()

        # self.lastOcclusionResult = Texture("LastOcclusionResult")
        # self.lastOcclusionResult.setup2dTexture(self.size.x / 2, self.size.y / 2, Texture.F_rgb)


    def _makeDeferredTargets(self):
        """ Creates the multi-render-target """
        self.debug("Creating deferred targets")
        self.deferredTarget = RenderTarget("DeferredTarget")
        self.deferredTarget.addColorAndDepth()

        if self.haveMRT:
            self.deferredTarget.addAuxTextures(3)
            self.deferredTarget.setAuxBits(16)
            self.deferredTarget.setColorBits(32)
            self.deferredTarget.setDepthBits(32)

        self.deferredTarget.prepareSceneRender()


    def _setupLastFrameTextures(self):

        self.lastFramePosition = Texture("LastFramePosition")
        self.lastFramePosition.setup2dTexture(self.size.x / 2, self.size.y / 2, Texture.TFloat, Texture.FRgba32)
        # self.lastFramePosition.setMinfilter(SamplerState.FTNearest)
        # self.lastFramePosition.setMagfilter(SamplerState.FTNearest)

        BufferViewerGUI.registerTexture("LastFramePosition", self.lastFramePosition)

        if self.haveOcclusion:
            self.lastFrameOcclusion = Texture("lastFrameOcclusion")
            self.lastFrameOcclusion.setup2dTexture(self.size.x / 2, self.size.y / 2, Texture.TFloat, Texture.FR16)
            BufferViewerGUI.registerTexture("lastFrameOcclusion", self.lastFrameOcclusion)
            # self.lastFrameOcclusion.setMinfilter(SamplerState.FTNearest)
            # self.lastFrameOcclusion.setMagfilter(SamplerState.FTNearest)



    def _setupFinalPass(self):
        """ Setups the final pass which applies motion blur and so on """
        # Set wrap for motion blur
        colorTex = self.antialias.getResultTexture()
        colorTex.setWrapU(SamplerState.WMClamp)
        colorTex.setWrapV(SamplerState.WMClamp)

        # Pass the color lut
        colorLUT = loader.loadTexture("Data/ColorLUT/" + self.settings.colorLookupTable)
        colorLUT.setWrapU(SamplerState.WMClamp)
        colorLUT.setWrapV(SamplerState.WMClamp)
        colorLUT.setFormat(Texture.F_rgb16)
        colorLUT.setMinfilter(SamplerState.FTLinear)
        colorLUT.setMagfilter(SamplerState.FTLinear)
        self.deferredTarget.setShaderInput("colorLUT", colorLUT)

        # Set the shader
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

    def _creatGIPrecomputeBuffer(self):
        """ Creates the half-resolution buffer which computes gi and gi
        reflections. We use half-res for performance """

        self.giPrecomputeBuffer = RenderTarget("GICompute")
        self.giPrecomputeBuffer.setSize(self.size.x / 2, self.size.y / 2)
        self.giPrecomputeBuffer.addColorTexture()
        self.giPrecomputeBuffer.addAuxTextures(1)
        self.giPrecomputeBuffer.setColorBits(16)
        self.giPrecomputeBuffer.prepareOffscreenBuffer()


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

        noiseTexture = self.showbase.loader.loadTexture("Data/Occlusion/noise4x4.png")
        noiseTexture.setMinfilter(SamplerState.FTNearest)
        noiseTexture.setMagfilter(SamplerState.FTNearest)

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
            self.lightingComputeContainer.setShaderInput(
                "mainCam", self.showbase.cam)
            self.lightingComputeContainer.setShaderInput(
                "mainRender", self.showbase.render)

            if self.occlusion.requiresViewSpacePosNrm():
                self.lightingComputeContainer.setShaderInput(
                    "viewSpaceNormals",
                    self.normalPrecompute.getColorTexture())
                self.lightingComputeContainer.setShaderInput(
                    "viewSpacePosition",
                    self.normalPrecompute.getAuxTexture(0))

            self.lightingComputeContainer.setShaderInput(
                "shadowAtlas", self.lightManager.getAtlasTex())

            if self.settings.useHardwarePCF:
                self.lightingComputeContainer.setShaderInput(
                    "shadowAtlasPCF", self.lightManager.getAtlasTex(), self.lightManager.getPCFSampleState())



            self.lightingComputeContainer.setShaderInput(
                "destination", self.lightingComputeCombinedTex)
            self.lightingComputeContainer.setShaderInput(
                "cameraPosition", self.cameraPosition)
            self.lightingComputeContainer.setShaderInput(
                "frameIndex", self.frameIndex)

            self.lightingComputeContainer.setShaderInput(
                "noiseTexture",
                noiseTexture)
            self.lightingComputeContainer.setShaderInput(
                "lightsPerTile", self.lightPerTileStorage)


            if self.settings.enableGlobalIllumination:
                self.lightingComputeContainer.setShaderInput("giDiffuseTex", self.giPrecomputeBuffer.getColorTexture())
                self.lightingComputeContainer.setShaderInput("giReflectionTex", self.giPrecomputeBuffer.getAuxTexture(0))


            self.lightingComputeContainer.setShaderInput("lastFramePosition", self.lastFramePosition)

            if self.haveOcclusion:
                self.lightingComputeContainer.setShaderInput("lastFrameOcclusion", self.lastFrameOcclusion)


        # Shader inputs for the occlusion blur passes
        if self.occlusion.requiresBlurring():
            self.blurOcclusionH.setShaderInput(
                "colorTex", self.blurOcclusionV.getColorTexture())
            self.blurOcclusionV.setShaderInput(
                "colorTex",
                self.lightingComputeContainer.getColorTexture())

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


        # Shader inputs for the final pass
        if self.blurEnabled:
            self.deferredTarget.setShaderInput(
                "colorTex", self.blurColorV.getColorTexture())
        else:
            self.deferredTarget.setShaderInput(
                "colorTex", self.antialias.getResultTexture())

        if self.occlusion.requiresBlurring() or self.occlusion.requiresViewSpacePosNrm():
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


        if self.haveOcclusion:
            if self.occlusion.requiresViewSpacePosNrm():
                self.occlusionBuffer.setShaderInput(
                    "viewSpaceNormals",
                    self.normalPrecompute.getColorTexture())
                self.occlusionBuffer.setShaderInput(
                    "viewSpacePosition",
                    self.normalPrecompute.getAuxTexture(0))

            self.occlusionBuffer.setShaderInput("mainCam", self.showbase.cam)
            self.occlusionBuffer.setShaderInput("mainRender", self.showbase.render)
            self.occlusionBuffer.setShaderInput(
                "frameIndex", self.frameIndex)

            self.occlusionBuffer.setShaderInput("depth", 
                self.deferredTarget.getDepthTexture())

            self.occlusionBuffer.setShaderInput("noiseTexture", noiseTexture)

            self.lightingComputeContainer.setShaderInput("occlusionTex", self.occlusionBuffer.getColorTexture())

            self.deferredTarget.setShaderInput("debugTex",
                                               self.antialias.getResultTexture())

        self.deferredTarget.setShaderInput(
            "currentPosition", self.deferredTarget.getColorTexture())


        self.deferredTarget.setShaderInput("lastFramePosition", self.lastFramePosition)
        self.deferredTarget.setShaderInput("currentFramePosition", self.deferredTarget.getColorTexture())




        
        if self.haveOcclusion:
            self.deferredTarget.setShaderInput("computedOcclusion", self.occlusionBuffer.getColorTexture())
            self.deferredTarget.setShaderInput("lastFrameOcclusion", self.lastFrameOcclusion)

        # Set last / current mvp handles
        self.showbase.render.setShaderInput("lastMVP", self.lastMVP)

        # Set GI inputs
        if self.settings.enableGlobalIllumination:
            self.globalIllum.bindTo(self.giPrecomputeBuffer, "giData")

            self.giPrecomputeBuffer.setShaderInput(
                "data0", self.deferredTarget.getColorTexture())
            self.giPrecomputeBuffer.setShaderInput(
                "data1", self.deferredTarget.getAuxTexture(0))
            self.giPrecomputeBuffer.setShaderInput(
                "data2", self.deferredTarget.getAuxTexture(1))
            self.giPrecomputeBuffer.setShaderInput(
                "data3", self.deferredTarget.getAuxTexture(2))
            self.giPrecomputeBuffer.setShaderInput(
                "cameraPosition", self.cameraPosition)

        # Finally, set shaders
        self.reloadShaders()

    def _loadFallbackCubemap(self):
        """ Loads the cubemap for image based lighting """
        cubemap = self.showbase.loader.loadCubeMap(
            self.settings.defaultReflectionCubemap)
        cubemap.setMinfilter(Texture.FTLinearMipmapLinear)
        cubemap.setMagfilter(Texture.FTLinearMipmapLinear)
        cubemap.setFormat(Texture.F_srgb)
        self.lightingComputeContainer.setShaderInput(
            "fallbackCubemap", cubemap)
        self.lightingComputeContainer.setShaderInput(
            "fallbackCubemapMipmaps", math.log(cubemap.getXSize(), 2))

    def _loadLookupCubemap(self):
        self.debug("Loading lookup cubemap")
        cubemap = self.showbase.loader.loadCubeMap(
            "Data/Cubemaps/DirectionLookup/#.png")
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
        self.lightingComputeContainer.setSize(self.size.x, self.size.y)

        self.lightingComputeContainer.addColorTexture()
        self.lightingComputeContainer.setColorBits(16)
        self.lightingComputeContainer.prepareOffscreenBuffer()

        self.lightingComputeCombinedTex = Texture("Lighting-Compute-Combined")
        self.lightingComputeCombinedTex.setup2dTexture(
            self.size.x, self.size.y, Texture.TFloat, Texture.FRgba8)
        self.lightingComputeCombinedTex.setMinfilter(Texture.FTLinear)
        self.lightingComputeCombinedTex.setMagfilter(Texture.FTLinear)

        self.lastPositionBuffer = Texture("Last-Position-Buffer")
        self.lastPositionBuffer.setup2dTexture(
            self.size.x, self.size.y, Texture.TFloat, Texture.FRgba16)
        self.lastPositionBuffer.setMinfilter(Texture.FTNearest)
        self.lastPositionBuffer.setMagfilter(Texture.FTNearest)

    def _createOcclusionBlurBuffer(self):
        """ Creates the buffers needed to blur the occlusion """
        self.blurOcclusionV = RenderTarget("OcclusionBlurVertical")
        self.blurOcclusionV.addColorTexture()
        self.blurOcclusionV.prepareOffscreenBuffer()

        self.blurOcclusionH = RenderTarget("OcclusionBlurHorizontal")
        self.blurOcclusionH.addColorTexture()
        self.blurOcclusionH.prepareOffscreenBuffer()

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
            self.size.x, self.size.y,
            Texture.TFloat, Texture.FRg16)

    def _setOcclusionBlurShader(self):
        """ Sets the shaders which blur the occlusion """
        blurVShader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/BlurOcclusionVertical.fragment")
        blurHShader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/BlurOcclusionHorizontal.fragment")
        self.blurOcclusionV.setShader(blurVShader)
        self.blurOcclusionH.setShader(blurHShader)

    def _setGIComputeShader(self):
        """ Sets the shader which computes the GI """
        giShader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/ComputeGI.fragment")
        self.giPrecomputeBuffer.setShader(giShader)

    def _setBlurShader(self):
        """ Sets the shaders which blur the color """
        blurVShader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/BlurVertical.fragment")
        blurHShader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/BlurHorizontal.fragment")
        self.blurColorV.setShader(blurVShader)
        self.blurColorH.setShader(blurHShader)

    def _setLightingShader(self):
        """ Sets the shader which applies the light """
        lightShader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/ApplyLighting.fragment")
        self.lightingComputeContainer.setShader(lightShader)

    def _setPositionComputationShader(self):
        """ Sets the shader which computes the lights per tile """
        pcShader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/PrecomputeLights.fragment")
        self.lightBoundsComputeBuff.setShader(pcShader)

    def _setFinalPassShader(self):
        """ Sets the shader which computes the final frame,
        with motion blur and so on """
        fShader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/Final.fragment")
        self.deferredTarget.setShader(fShader)

    def _setOcclusionShader(self):
        """ Sets the shader to precompute the occlusion """
        oShader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/ComputeOcclusion.fragment")
        self.occlusionBuffer.setShader(oShader)


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

        self._setFinalPassShader()

        if self.settings.enableGlobalIllumination:
            self._setGIComputeShader()

        if self.occlusion.requiresBlurring():
            self._setOcclusionBlurShader()

        if self.haveOcclusion:
            self._setOcclusionShader()

        if self.blurEnabled:
            self._setBlurShader()

        if self.occlusion.requiresViewSpacePosNrm():
            self._setNormalExtractShader()

        self.antialias.reloadShader()
        if self.settings.enableGlobalIllumination:
            self.globalIllum.reloadShader()

    def _setNormalExtractShader(self):
        """ Sets the shader which constructs the normals from position """
        npShader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/ExtractNormals.fragment")
        self.normalPrecompute.setShader(npShader)

    def _attachUpdateTask(self):
        """ Attaches the update tasks to the showbase """

        self.showbase.addTask(
            self._preRenderCallback, "RP_BeforeRender", sort=-5000)

        self.showbase.addTask(
            self._update, "RP_Update", sort=-10)

        if self.haveLightingPass:
            self.showbase.addTask(
                self._updateLights, "RP_UpdateLights", sort=-9)
            self.showbase.addTask(
                self._updateShadows, "RP_UpdateShadows", sort=-8)

            self.showbase.addTask(
                self._processShadowCallbacks, "RP_ShadowCallbacks", sort=-5)


        if self.settings.displayOnscreenDebugger:
            self.showbase.addTask(
                self._updateGUI, "RP_UpdateGUI", sort=7)

        self.showbase.addTask(
            self._postRenderCallback, "RP_AfterRender", sort=5000)

    def _preRenderCallback(self, task=None):
        """ Called before rendering """

        if self.settings.enableGlobalIllumination:
            self.globalIllum.process()
        
        self.antialias.preRenderUpdate()

        if task is not None:
            return task.cont

    def _postRenderCallback(self, task=None):
        """ Called after rendering """

        self.antialias.postRenderUpdate()
        self.frameIndex[0] += 1

        if task is not None:
            return task.cont

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

    def _processShadowCallbacks(self, task=None):
        self.lightManager.processCallbacks()
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

        self.currentShiftIndex[0] = 1 - self.currentShiftIndex[0]

        currentFPS = 1.0 / self.showbase.taskMgr.globalClock.getDt()
        self.cameraPosition[0] = self.showbase.cam.getPos(self.showbase.render)
        self.motionBlurFactor[0] = min(1.5, currentFPS /
                                       60.0) * self.settings.motionBlurFactor

        self.cullBounds = self._computeCameraBounds()

        if self.haveLightingPass:
            self.lightManager.setCullBounds(self.cullBounds)

        self.lastMVP[0] = self.currentMVP[0]
        self.currentMVP[0] = self._computeMVP()

        shift = self.pixelShifts[self.currentShiftIndex[0]]
        self.lastPixelShift[0] = self.currentPixelShift[0]
        self.currentPixelShift[0] = shift
        Globals.base.camLens.setFilmOffset(shift.x, shift.y)

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
            shader = Shader.load(Shader.SLGLSL, 
                "Shader/DefaultObjectShader/vertex.glsl",
                "Shader/DefaultObjectShader/fragment.glsl")
        else:
            self.warn(
                "Tesselation is only experimental! Remember "
                "to convert the geometry to patches first!")

            shader = Shader.load(Shader.SLGLSL, 
                "Shader/DefaultObjectShader/vertex.glsl",
                "Shader/DefaultObjectShader/fragment.glsl",
                "",
                "Shader/DefaultObjectShader/tesscontrol.glsl",
                "Shader/DefaultObjectShader/tesseval.glsl")

        return shader


    def getDefaultSkybox(self, scale=40000):
        """ Loads the skybox """
        skybox = loader.loadModel("Models/Skybox/Model.egg.bam")
        skybox.setScale(scale)

        skytex = loader.loadTexture("Data/Skybox/Sky.jpg")
        skytex.setWrapU(SamplerState.WMRepeat)
        skytex.setWrapV(SamplerState.WMRepeat)
        skytex.setMinfilter(SamplerState.FTLinear)
        skytex.setMagfilter(SamplerState.FTLinear)
        skybox.setShaderInput("skytex", skytex)

        skybox.setShader(Shader.load(Shader.SLGLSL, 
                "Shader/DefaultObjectShader/vertex.glsl", "Shader/Skybox/fragment.glsl"))
        return skybox

    def _getDeferredBuffer(self):
        """ Returns a handle to the internal deferred target """
        return self.deferredTarget.getInternalBuffer()

    def addLight(self, light):
        """ Adds a light to the list of rendered lights """
        if self.haveLightingPass:
            self.lightManager.addLight(light)
        else:
            self.warn("Lighting is disabled, so addLight has no effect")

    def setScattering(self, scatteringModel):
        """ Sets a scattering model to use. Only has an effect if enableScattering
        is enabled """
        self.debug("Loading scattering model ..")
        if not self.settings.enableScattering:
            self.error("You cannot set a scattering model as scattering is not"
                        " enabled in your pipeline.ini!")
            return

        self.lightingComputeContainer.setShaderInput(
            "transmittanceSampler", scatteringModel.getTransmittanceResult())
        self.lightingComputeContainer.setShaderInput(
            "inscatterSampler", scatteringModel.getInscatterTexture())
        scatteringModel.bindTo(
            self.lightingComputeContainer, "scatteringOptions")

    def enableDefaultEarthScattering(self):
        """ Adds a standard scattering model, representing the atmosphere of
        the earth. This is a shortcut for creating a Scattering instance and
        precomputing it """
        earthScattering = Scattering()

        scale = 1000000000
        earthScattering.setSettings({
            "atmosphereOffset": Vec3(0, 0, - (6360.0 + 9.5) * scale),
            "atmosphereScale": Vec3(scale)
        })
        earthScattering.precompute()
        self.setScattering(earthScattering)


    def setGILightSource(self, light):
        """ Sets the light source for the global illumination. The GI uses this
        light to shade the voxels, so this light is the only light which "casts"
        global illumination. When GI is disabled, this has no effect """

        if self.settings.enableGlobalIllumination:
            self.globalIllum.setTargetLight(light)

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

        defines.append(("AMBIENT_CUBEMAP_SAMPLES", self.settings.ambientCubemapSamples))

        defines.append(
            ("SHADOW_MAP_ATLAS_SIZE", self.settings.shadowAtlasSize))
        defines.append(
            ("SHADOW_MAX_UPDATES_PER_FRAME", self.settings.maxShadowUpdatesPerFrame))
        defines.append(
            ("SHADOW_GEOMETRY_MAX_VERTICES", self.settings.maxShadowUpdatesPerFrame * 3))


        defines.append(("SHADOW_NUM_PCF_SAMPLES", self.settings.numPCFSamples))
        defines.append(("SHADOW_NUM_PCSS_SEARCH_SAMPLES", self.settings.numPCSSSearchSamples))
        defines.append(("SHADOW_NUM_PCSS_FILTER_SAMPLES", self.settings.numPCSSFilterSamples))

        defines.append(("SHADOW_PSSM_BORDER_PERCENTAGE", self.settings.shadowCascadeBorderPercentage))

        if self.settings.useHardwarePCF:
            defines.append(("USE_HARDWARE_PCF", 1))

        defines.append(("WINDOW_WIDTH", self.size.x))
        defines.append(("WINDOW_HEIGHT", self.size.y))

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

        if self.settings.enableGlobalIllumination:
            defines.append(("USE_GLOBAL_ILLUMINATION", 1))

        if self.settings.enableScattering:
            defines.append(("USE_SCATTERING", 1))

        if self.haveOcclusion:
            defines.append(("USE_OCCLUSION", 1))


        # Pass near far
        defines.append(("CAMERA_NEAR", Globals.base.camLens.getNear()))
        defines.append(("CAMERA_FAR", Globals.base.camLens.getFar()))


        # Make sure the configuration file stamp is changed
        defines.append(("RANDOM_TIMESTAMP", random.random()))

        # Generate
        output = "#pragma once\n"
        output += "// Autogenerated by RenderingPipeline.py\n"
        output += "// Do not edit! Your changes will be lost.\n\n"

        for key, value in defines:
            output += "#define " + key + " " + str(value) + "\n"

        # Try to write the file

        try:
            with open("PipelineTemp/ShaderAutoConfig.include", "w") as handle:
                handle.write(output)
        except Exception, msg:
            self.fatal("Error writing shader autoconfig. Maybe no write-access?")
            return

    def onWindowResized(self):
        """ Call this whenever the window resized """
        raise NotImplementedError()

    def destroy(self):
        """ Call this when you want to shut down the pipeline """
        self.mountManager.unmount()
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
