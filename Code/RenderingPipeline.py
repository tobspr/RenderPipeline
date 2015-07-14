

from panda3d.core import NodePath, Shader, Vec4, TransparencyAttrib, LVecBase2i
from panda3d.core import PTAVecBase3f, PTAFloat, PTALMatrix4f, PTAInt, SamplerState
from panda3d.core import CSYupRight, TransformState, Mat4, CSZupRight, BitMask32
from panda3d.core import Texture, UnalignedLMatrix4f, Vec3, PTAFloat, TextureStage
from panda3d.core import ColorWriteAttrib

from DebugObject import DebugObject
from SystemAnalyzer import SystemAnalyzer
from Scattering import Scattering
from Globals import Globals
from GlobalIllumination import GlobalIllumination
from EffectLoader import EffectLoader

from PipelineSettingsManager import PipelineSettingsManager
from LightManager import LightManager
from MountManager import MountManager
from RenderPassManager import RenderPassManager
from AmbientOcclusionManager import AmbientOcclusionManager
from AntialiasingManager import AntialiasingManager
from TransparencyManager import TransparencyManager
from DynamicObjectsManager import DynamicObjectsManager
from GUI.PipelineGuiManager import PipelineGuiManager

from RenderPasses.InitialRenderPass import InitialRenderPass
from RenderPasses.DeferredScenePass import DeferredScenePass
from RenderPasses.ViewSpacePass import ViewSpacePass
from RenderPasses.LightingPass import LightingPass
from RenderPasses.DynamicExposurePass import DynamicExposurePass
from RenderPasses.FinalPostprocessPass import FinalPostprocessPass
from RenderPasses.VolumetricLightingPass import VolumetricLightingPass
from RenderPasses.SSLRPass import SSLRPass

class RenderingPipeline(DebugObject):

    """ This is the main rendering pipeline module. It setups the whole pipeline
    process, as well as creating the managers for the different effects/passes.
    It also handles some functions to prepare the scene, e.g. for tesselation.
    """

    def __init__(self, showbase):
        """ Creates a new pipeline """
        DebugObject.__init__(self, "RenderingPipeline")
        self.showbase = showbase
        self.settings = None
        self.ready = False
        self.mountManager = MountManager()

    def getMountManager(self):
        """ Returns the mount manager. You can use this to set the
        write directory and base path """
        return self.mountManager

    def loadSettings(self, filename):
        """ Loads the pipeline settings from an ini file """
        self.settings = PipelineSettingsManager()
        self.settings.loadFromFile(filename)

        # This has to be here, before anything is printed
        DebugObject.setOutputLevel(self.settings.pipelineOutputLevel)

    def getSettings(self):
        """ Returns the current pipeline settings """
        return self.settings

    def addLight(self, light):
        """ Attaches a new light to the pipeline, this just forwards the call to
        the light manager. """
        self.lightManager.addLight(light)

    def removeLight(self, light):
        """ Removes a light from the pipeline, this just forwards the call to
        the light manager. """
        self.lightManager.removeLight(light)

    def onSceneInitialized(self):
        """ Tells the pipeline that the scene is ready to be rendered. This starts
        shadow updates """
        self.ready = True

    def setGILightSource(self, lightSource):
        """ Sets the light used to compute GI. For now, only directional lights
        can cast GI. """
        if self.settings.enableGlobalIllumination:
            self.globalIllum.setTargetLight(lightSource)

    def setScatteringSource(self, lightSource):
        """ Sets the light source used for the scattering, can be a point or 
        directional light """
        if self.settings.enableScattering:
            self.scattering.setSunLight(lightSource)

    def getMainPassBitmask(self):
        """ Returns the camera bit used to render the main scene """
        return BitMask32.bit(2)

    def getShadowPassBitmask(self):
        """ Returns the camera bit used to render the shadow scene """
        return BitMask32.bit(3)

    def getVoxelizePassBitmask(self):
        """ Returns the camera bit used to voxelize the scene for GI """
        return BitMask32.bit(4)

    def setEffect(self, obj, effect, properties = None, sort=0):
        """ Applies the effect to an object with the given properties """

        effect = self.effectLoader.loadEffect(effect, properties)

        if effect.getSetting("transparent"):
            pass

        if effect.getSetting("dynamic"):
            self.registerDynamicObject(obj)

        if not effect.getSetting("castShadows"):
            obj.hide(self.getShadowPassBitmask())

        if not effect.getSetting("castGI"):
            obj.hide(self.getVoxelizePassBitmask())

        obj.setShader(effect.getShader("Default"), sort)

        # Create shadow caster state
        if effect.getSetting("castShadows"):
            initialState = NodePath("EffectInitialState")
            initialState.setShader(effect.getShader("Shadows"), sort)
            initialState.setAttrib(ColorWriteAttrib.make(ColorWriteAttrib.COff))
            stateName = "NodeEffect-" + str(effect.getEffectID())
            self.lightManager.shadowPass.registerTagState(stateName, initialState.getState())
            obj.setTag("ShadowPassShader", stateName)

    def fillTextureStages(self, nodePath):
        """ Prepares all materials of a given nodepath to have at least the 4 
        default textures in the correct order: [diffuse, normal, specular, roughness] """
        
        emptyDiffuseTex = loader.loadTexture("Data/Textures/EmptyDiffuseTexture.png")
        emptyNormalTex = loader.loadTexture("Data/Textures/EmptyNormalTexture.png")
        emptySpecularTex = loader.loadTexture("Data/Textures/EmptySpecularTexture.png")
        emptyRoughnessTex = loader.loadTexture("Data/Textures/EmptyRoughnessTexture.png")

        textureOrder = [emptyDiffuseTex, emptyNormalTex, emptySpecularTex, emptyRoughnessTex]
        textureSorts = [0, 10, 20, 30]

        # Prepare the textures
        for tex in textureOrder:
            tex.setMinfilter(SamplerState.FTLinear)
            tex.setMagfilter(SamplerState.FTLinear)
            tex.setFormat(Texture.FRgba)

        # Iterate over all geom nodes
        for np in nodePath.findAllMatches("**/+GeomNode"):

            # Check how many texture stages the nodepath already has
            stages = np.findAllTextureStages()
            numStages = len(stages)

            # Fill the texture stages up
            for i in xrange(numStages, 4):
                stage = TextureStage("DefaultTexStage" + str(i))
                stage.setSort(textureSorts[i])
                stage.setMode(TextureStage.CMModulate)
                stage.setColor(Vec4(0, 0, 0, 1))
                np.setTexture(stage, textureOrder[i])

    def registerDynamicObject(self, np):
        """ Registers a new dynamic object to the pipeline. Every object which moves
        or transforms its vertices (like actors) has to be registered to make sure
        the velocity buffers are correct. When the object is deleted, 
        unregisterDynamicObject should be called. """
        self.dynamicObjectsManager.registerObject(np)

    def unregisterDynamicObject(self, np):
        """ Unregisters a dynamic object which was previously registered with
        registerDynamicObject """
        self.dynamicObjectsManager.unregisterObject(np)

    def getDefaultSkybox(self, scale=40000):
        """ Loads the default skybox, scaling it by the given scale factor. Note
        that there should always be a noticeable difference between the skybox
        scale and the camera far plane, to avoid z-fighting issues. The default
        skybox also comes with a default skybox shader aswell as a default skybox
        texture. The shaders and textures can be overridden by the user if required. """
        skybox = loader.loadModel("Models/Skybox/Model.egg.bam")
        skybox.setScale(scale)

        skytex = loader.loadTexture("Data/Skybox/sky.jpg")
        skytex.setWrapU(SamplerState.WMRepeat)
        skytex.setWrapV(SamplerState.WMRepeat)
        skytex.setMinfilter(SamplerState.FTLinear)
        skytex.setMagfilter(SamplerState.FTLinear)
        skybox.setShaderInput("skytex", skytex)
        self.setEffect(skybox, "Effects/Default/Skybox.effect", {
            "castShadows": False, 
            "normalMapping": False, 
            "castGI": False}, 100)
        skybox.setName("Skybox")
        return skybox

    def reloadShaders(self):
        """ Reloads all shaders and regenerates all intitial states. This function
        also updates the shader autoconfig """
        self.debug("Reloading shaders")
        self.renderPassManager.writeAutoconfig()
        self.renderPassManager.setShaders()

        if self.settings.enableGlobalIllumination:
            self.globalIllum.reloadShader()

    def getRenderPassManager(self):
        """ Returns a handle to the render pass manager attribute """
        return self.renderPassManager

    def getSize(self):
        """ Returns the window size """
        return self._size

    def _createTasks(self):
        """ Spanws the pipeline update tasks, this are mainly the pre-render
        and post-render tasks, whereas the pre-render task has a lower priority
        than the draw task, and the post-render task has a higher priority. """
        self.showbase.addTask(self._preRenderUpdate, "RP_BeforeRender", sort=-5000)
        self.showbase.addTask(self._postRenderUpdate, "RP_AfterRender", sort=5000)

    def _createInputHandles(self):
        """ Defines various inputs to be used in the shader passes. Most inputs
        use pta-arrays, so updating them is faster than using setShaderInput all the
        time. """
        self.cameraPosition = PTAVecBase3f.emptyArray(1)
        self.currentViewMat = PTALMatrix4f.emptyArray(1)
        self.lastMVP = PTALMatrix4f.emptyArray(1)
        self.currentMVP = PTALMatrix4f.emptyArray(1)
        self.frameIndex = PTAInt.emptyArray(1)
        self.frameDelta = PTAFloat.emptyArray(1)

        self.renderPassManager.registerStaticVariable("lastMVP", self.lastMVP)
        self.renderPassManager.registerStaticVariable("currentMVP", self.currentMVP)
        self.renderPassManager.registerStaticVariable("frameIndex", self.frameIndex)
        self.renderPassManager.registerStaticVariable("cameraPosition", self.cameraPosition)
        self.renderPassManager.registerStaticVariable("mainCam", self.showbase.cam)
        self.renderPassManager.registerStaticVariable("mainRender", self.showbase.render)
        self.renderPassManager.registerStaticVariable("frameDelta", self.frameDelta)
        self.renderPassManager.registerStaticVariable("currentViewMat", self.currentViewMat)

        # self.transformMat = TransformState.makeMat(Mat4.convertMat(Globals.base.win.getGsg().getInternalCoordinateSystem(), CSZupRight))
        self.transformMat = TransformState.makeMat(Mat4.convertMat(CSYupRight, CSZupRight))


    def _preRenderUpdate(self, task):
        """ This is the pre render task which handles updating of all the managers
        as well as calling the pipeline update task """
        if not self.ready:
            return task.cont
        self._updateInputHandles()
        self.lightManager.update()
        if self.guiManager:
            self.guiManager.update()
        if self.transparencyManager:
            self.transparencyManager.update()
        self.antialiasingManager.update()
        self.renderPassManager.preRenderUpdate()
        if self.globalIllum:
            self.globalIllum.update()
        if self.scattering:
            self.scattering.update()
        self.dynamicObjectsManager.update()

        return task.cont

    def _updateInputHandles(self):
        """ Updates the input-handles on a per frame basis defined in 
        _createInputHandles """
        # Compute camera bounds
        cameraBounds = self.showbase.camNode.getLens().makeBounds()
        cameraBounds.xform(self.showbase.camera.getMat(self.showbase.render))
        self.lightManager.setCullBounds(cameraBounds)

        self.lastMVP[0] = self.currentMVP[0]
        self.currentMVP[0] = self._computeMVP()
        self.currentViewMat[0] = UnalignedLMatrix4f(self.transformMat.invertCompose(self.showbase.render.getTransform(self.showbase.cam)).getMat())
        self.frameDelta[0] = Globals.clock.getDt()
        self.cameraPosition[0] = self.showbase.cam.getPos(self.showbase.render)
        self.frameIndex[0] = self.frameIndex[0] + 1

    def _computeMVP(self):
        """ Computes the current scene mvp. Actually, this is the
        worldViewProjectionMatrix, but for convience it's called mvp. """
        camLens = self.showbase.camLens
        projMat = camLens.getProjectionMat()
        modelViewMat = self.showbase.render.getTransform(self.showbase.cam).getMat()
        return UnalignedLMatrix4f(modelViewMat * projMat)

    def _postRenderUpdate(self, task):
        """ This is the post render update, being called after the draw task. """
        if not self.ready:
            return task.cont
        return task.cont

    def _createViewSpacePass(self):
        """ Creates a pass which computes the view space normals and position.
        This pass is only created if any render pass requires the provided
        inputs """
        if self.renderPassManager.anyPassRequires("ViewSpacePass.normals") or \
            self.renderPassManager.anyPassRequires("ViewSpacePass.position"):
            self.viewSpacePass = ViewSpacePass()
            self.renderPassManager.registerPass(self.viewSpacePass)

    def _createDefaultTextureInputs(self):
        """ This method loads various textures used in the different render passes
        and provides them as inputs to the render pass manager """
        for color in ["White", "Black"]:
            emptyTex = loader.loadTexture("Data/Textures/" + color + ".png")
            emptyTex.setMinfilter(SamplerState.FTLinear)
            emptyTex.setMagfilter(SamplerState.FTLinear)
            emptyTex.setWrapU(SamplerState.WMClamp)
            emptyTex.setWrapV(SamplerState.WMClamp)
            self.renderPassManager.registerStaticVariable("emptyTexture" + color, emptyTex)

        texNoise = loader.loadTexture("Data/Textures/noise4x4.png")
        texNoise.setMinfilter(SamplerState.FTNearest)
        texNoise.setMagfilter(SamplerState.FTNearest)
        self.renderPassManager.registerStaticVariable("noise4x4", texNoise)


        # Load the cubemap which is used for point light shadow rendering
        cubemapLookup = self.showbase.loader.loadCubeMap(
            "Data/Cubemaps/DirectionLookup/#.png")
        cubemapLookup.setMinfilter(SamplerState.FTNearest)
        cubemapLookup.setMagfilter(SamplerState.FTNearest)
        cubemapLookup.setFormat(Texture.FRgb8)
        self.renderPassManager.registerStaticVariable("directionToFaceLookup", 
            cubemapLookup)

        # Load the default environment cubemap
        cubemapEnv = self.showbase.loader.loadCubeMap(
            self.settings.defaultReflectionCubemap, readMipmaps=True)
        cubemapEnv.setMinfilter(SamplerState.FTLinearMipmapLinear)
        cubemapEnv.setMagfilter(SamplerState.FTLinearMipmapLinear)
        cubemapEnv.setFormat(Texture.FRgba)
        self.renderPassManager.registerStaticVariable("defaultEnvironmentCubemap", 
            cubemapEnv)
        self.renderPassManager.registerStaticVariable("defaultEnvironmentCubemapMipmaps", 
            cubemapEnv.getExpectedNumMipmapLevels())

        # Load the color LUT
        colorLUT = loader.loadTexture("Data/ColorLUT/" + self.settings.colorLookupTable)
        colorLUT.setWrapU(SamplerState.WMClamp)
        colorLUT.setWrapV(SamplerState.WMClamp)
        colorLUT.setFormat(Texture.F_rgb16)
        colorLUT.setMinfilter(SamplerState.FTLinear)
        colorLUT.setMagfilter(SamplerState.FTLinear)
        self.renderPassManager.registerStaticVariable("colorLUT", colorLUT)

    def _createGenericDefines(self):
        """ Registers some of the configuration defines, mainly specified in the
        pipeline config, at the render pass manager """
        define = lambda name, val: self.renderPassManager.registerDefine(name, val)
        define("WINDOW_WIDTH", self._size.x)
        define("WINDOW_HEIGHT", self._size.y)

        if self.settings.displayOnscreenDebugger:
            define("DEBUGGER_ACTIVE", 1)

        if self.settings.enableGlobalIllumination:
            define("USE_GLOBAL_ILLUMINATION", 1)

        # TODO: Move to scattering module
        if self.settings.enableScattering:
            define("USE_SCATTERING", 1)


        define("GLOBAL_AMBIENT_FACTOR", self.settings.globalAmbientFactor)

        # TODO: Add sslr
        # if self.settings.enableSSLR:
        #     define("USE_SSLR", 1)

        # Pass camera near and far plane
        define("CAMERA_NEAR", Globals.base.camLens.getNear())
        define("CAMERA_FAR", Globals.base.camLens.getFar())

    def _createGlobalIllum(self):
        """ Creates the global illumination manager if enabled in the settings """
        if self.settings.enableGlobalIllumination:
            self.globalIllum = GlobalIllumination(self)
            self.globalIllum.setup()
        else:
            self.globalIllum = None

    def _precomputeScattering(self):
        """ Precomputes the scattering model for the default atmosphere if
        if specified in the settings """
        if self.settings.enableScattering:
            earthScattering = Scattering(self)
            scale = 100000
            earthScattering.setSettings({
                "atmosphereOffset": Vec3(0, 0, - (6360.0 + 16.5) * scale),
                "atmosphereScale": Vec3(scale)
            })
            earthScattering.precompute()
            earthScattering.provideInputs()

            self.scattering = earthScattering
        else:
            self.scattering = None

    def getScattering(self):
        """ Returns the scattering instance if scattering is enabled, otherwise
        throws an exception """
        if not self.settings.enableScattering:
            raise Exception("Scattering is not enabled, you can not fetch the scattering instance.")
        return self.scattering


    def recreate(self):
        """ Destroys and recreates the pipeline, preserving all lights """
        raise NotImplementedError()

    def destroy(self):
        """ Destroys the pipeline, cleaning up all buffers and textures """
        raise NotImplementedError()

    def create(self):
        """ Creates the pipeline """

        self.debug("Setting up render pipeline")

        # Handy shortcut
        self.showbase.accept("r", self.reloadShaders)

        if self.settings is None:
            self.error("You have to call loadSettings first!")
            return

        self.debug("Checking required Panda3D version ..")
        SystemAnalyzer.checkPandaVersionOutOfDate(29,04,2015)

        # Mount everything first
        self.mountManager.mount()

        # Check if there is already another instance running, but only if specified
        # in the settings
        if self.settings.preventMultipleInstances and not self.mountManager.getLock():
            self.fatal("Another instance of the rendering pipeline is already running")
            return

        # Store globals, as cython can't handle them
        self.debug("Setting up globals")
        Globals.load(self.showbase)
        Globals.font = loader.loadFont("Data/Font/SourceSansPro-Semibold.otf")
        Globals.font.setPixelsPerUnit(25)

        self._size = LVecBase2i(self.showbase.win.getXSize(), self.showbase.win.getYSize())

        # Check size
        if self._size.x % 2 == 1:
            self.fatal(
                "The window width has to be a multiple of 2 "
                "(Current: ", self._size.x, ")")
            return

        if self.settings.displayOnscreenDebugger:
            self.guiManager = PipelineGuiManager(self)
        else:
            self.guiManager = None

        # Some basic scene settings
        self.showbase.camLens.setNearFar(0.1, 500000)
        self.showbase.camLens.setFov(110)
        self.showbase.win.setClearColor(Vec4(1.0, 0.0, 1.0, 1.0))
        self.showbase.camNode.setCameraMask(self.getMainPassBitmask())
        self.showbase.render.setAttrib(TransparencyAttrib.make(TransparencyAttrib.MNone), 100)

        # Create render pass matcher
        self.renderPassManager = RenderPassManager()


        self._precomputeScattering()

        # Add initial pass
        self.initialRenderPass = InitialRenderPass()
        self.renderPassManager.registerPass(self.initialRenderPass)

        # Add deferred pass
        self.deferredScenePass = DeferredScenePass()
        self.renderPassManager.registerPass(self.deferredScenePass)

        # Add lighting pass
        self.lightingPass = LightingPass()
        self.renderPassManager.registerPass(self.lightingPass)

        # Add dynamic exposure pass
        if self.settings.useAdaptiveBrightness:
            self.dynamicExposurePass = DynamicExposurePass(self)
            self.renderPassManager.registerPass(self.dynamicExposurePass)

        # Add SSLR pass
        if self.settings.enableSSLR:
            self.sslrPass = SSLRPass()
            self.renderPassManager.registerPass(self.sslrPass)

        # Add volumetric lighting
        # self.volumetricLightingPass = VolumetricLightingPass()
        # self.renderPassManager.registerPass(self.volumetricLightingPass)

        # Add final pass
        self.finalPostprocessPass = FinalPostprocessPass()
        self.renderPassManager.registerPass(self.finalPostprocessPass)

        # Create managers
        self.occlusionManager = AmbientOcclusionManager(self)
        self.lightManager = LightManager(self)
        self.antialiasingManager = AntialiasingManager(self)
        self.dynamicObjectsManager = DynamicObjectsManager(self)
        
        if self.settings.useTransparency:
            self.transparencyManager = TransparencyManager(self)
        else:
            self.transparencyManager = None


        self._createGlobalIllum()

        # Make variables available
        self._createGenericDefines()
        self._createInputHandles()
        self._createDefaultTextureInputs()
        self._createViewSpacePass()

        # Finally matchup all the render passes and set the shaders
        self.renderPassManager.createPasses()
        self.renderPassManager.writeAutoconfig()
        self.renderPassManager.setShaders()

        # Create the update tasks
        self._createTasks()

        # Create the effect loader
        self.effectLoader = EffectLoader(self)

        # Apply the default effect to the scene
        self.setEffect(Globals.render, "Effects/Default/Default.effect", {
            "transparent": False,
            "normalMapping": False,
            "alphaTest": True,

            }, -10)

        if self.settings.enableGlobalIllumination:
            self.globalIllum.reloadShader()

        # Give the gui a hint when the pipeline is done loading
        if self.guiManager:
            self.guiManager.onPipelineLoaded()

        self.reloadShaders()