
import math
import struct

from panda3d.core import Texture, Camera, Vec3, Vec2, NodePath, RenderState
from panda3d.core import Shader, GeomEnums
from panda3d.core import CullFaceAttrib, ColorWriteAttrib, DepthWriteAttrib
from panda3d.core import OmniBoundingVolume, PTAInt, Vec4, PTAVecBase4f
from panda3d.core import LVecBase2i, ShaderAttrib, UnalignedLVecBase4f
from panda3d.core import ComputeNode, LVecBase4i, GraphicsOutput, SamplerState
from panda3d.core import Shader, Filename

from Light import Light
from DebugObject import DebugObject
from RenderTarget import RenderTarget
from ShadowSource import ShadowSource
from ShadowAtlas import ShadowAtlas
from ShaderStructArray import ShaderStructArray
from Globals import Globals
from MemoryMonitor import MemoryMonitor
from panda3d.core import PStatCollector

pstats_ProcessLights = PStatCollector("App:LightManager:ProcessLights")
pstats_CullLights = PStatCollector("App:LightManager:CullLights")
pstats_PerLightUpdates = PStatCollector("App:LightManager:PerLightUpdates")
pstats_FetchShadowUpdates = PStatCollector(
    "App:LightManager:FetchShadowUpdates")
pstats_WriteBuffers = PStatCollector("App:LightManager:WriteBuffers")


class LightManager(DebugObject):

    """ This class is internally used by the RenderingPipeline to handle
    Lights and their Shadows. It stores a list of lights, and updates the
    required ShadowSources per frame. There are two main update methods:

    updateLights processes each light and does a basic frustum check.
    If the light is in the frustum, its ID is passed to the light precompute
    container (set with setLightingCuller). Also, each shadowSource of
    the light is checked, and if it reports to be invalid, it's queued to
    the list of queued shadow updates.

    updateShadows processes the queued shadow updates and setups everything
    to render the shadow depth textures to the shadow atlas.

    Lights can be added with addLight. Notice you cannot change the shadow
    resolution or wether the light casts shadows after you called addLight.
    This is because it might already have a position in the atlas, and so
    the atlas would have to delete it's map, which is not supported (yet).
    This shouldn't be an issue, as you usually always know before if a
    light will cast shadows or not.

    """

    def __init__(self, pipeline):
        """ Creates a new LightManager. It expects a RenderPipeline as parameter. """
        DebugObject.__init__(self, "LightManager")

        
        # If you change this, don't forget to change it also in
        # Shader/Includes/Configuration.include!
        self.maxLights = {
            "PointLight": 15,
            "PointLightShadow": 3,
            "DirectionalLight": 1,
            "DirectionalLightShadow": 1,
            "SpotLight": 3,
            "SpotLightShadow": 1,
            "GIHelperLightShadow": 10
        }

        self.maxPerTileLights = {
            "PointLight": 15,
            "PointLightShadow": 3,
            "DirectionalLight": 1,
            "DirectionalLightShadow": 1,
            "SpotLight": 3,
            "SpotLightShadow": 1,
        }


        self.maxTotalLights = 20
        self.renderedLights = {}
        self.pipeline = pipeline
        self.settings = pipeline.getSettings()

        # Create arrays to store lights & shadow sources
        self.lights = []
        self.shadowSources = []
        self.queuedShadowUpdates = []
        self.allLightsArray = ShaderStructArray(Light, self.maxTotalLights)
        self.updateCallbacks = []

        self.cullBounds = None
        self.shadowScene = Globals.render

        # Create atlas
        self.shadowAtlas = ShadowAtlas()
        self.shadowAtlas.setSize(self.settings.shadowAtlasSize)
        self.shadowAtlas.create()

        self.maxShadowMaps = 24
        self.maxShadowUpdatesPerFrame = self.settings.maxShadowUpdatesPerFrame
        self.numShadowUpdatesPTA = PTAInt.emptyArray(1)

        self.updateShadowsArray = ShaderStructArray(
            ShadowSource, self.maxShadowUpdatesPerFrame)
        self.allShadowsArray = ShaderStructArray(
            ShadowSource, self.maxShadowMaps)

        # Create shadow compute buffer
        self._createShadowComputationBuffer()

        # Create the initial shadow state
        self.shadowComputeCamera.setTagStateKey("ShadowPassShader")
        self._createTagStates()
        self.shadowScene.setTag("ShadowPassShader", "Default")

        # Create debug overlay
        self._createDebugTexts()

        # Disable buffer on start
        self.shadowComputeTarget.setActive(False)

        # Bind arrays
        self.updateShadowsArray.bindTo(self.shadowScene, "updateSources")
        self.updateShadowsArray.bindTo(
            self.shadowComputeTarget, "updateSources")

        # Set initial inputs
        for target in [self.shadowComputeTarget, self.shadowScene]:
            target.setShaderInput("numUpdates", self.numShadowUpdatesPTA)

        self.lightingComputator = None
        self.lightCuller = None
        self.skip = 0
        self.skipRate = 0


    def _createTagStates(self):
        # Create shadow caster shader
        self.shadowCasterShader = Shader.load(Shader.SLGLSL,
            "Shader/DefaultShaders/ShadowCasting/vertex.glsl",
            "Shader/DefaultShaders/ShadowCasting/fragment.glsl",
            "Shader/DefaultShaders/ShadowCasting/geometry.glsl")
        initialState = NodePath("ShadowCasterState")
        initialState.setShader(self.shadowCasterShader, 30)
        # initialState.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullNone))
        initialState.setAttrib(ColorWriteAttrib.make(ColorWriteAttrib.COff))
        self.shadowComputeCamera.setTagState(
            "Default", initialState.getState())

    def _setLightCullingShader(self):
        """ Sets the shader which computes the lights per tile """
        pcShader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/PrecomputeLights.fragment")
        self.lightBoundsComputeBuff.setShader(pcShader)

    def getLightPerTileBuffer(self):
        return self.lightPerTileBuffer

    def initLightCulling(self):
        """ Creates the buffer which gets a list of lights and computes which
        light affects which tile """

        # Fetch patch size
        self.patchSize = LVecBase2i(
            self.settings.computePatchSizeX,
            self.settings.computePatchSizeY)

        # size has to be a multiple of the compute unit size
        # but still has to cover the whole screen
        sizeX = int(math.ceil(float(self.pipeline.size.x) / self.patchSize.x))
        sizeY = int(math.ceil(float(self.pipeline.size.y) / self.patchSize.y))

        self.precomputeSize = LVecBase2i(sizeX, sizeY)

        self.debug("Batch size =", sizeX, "x", sizeY,
                   "Actual Buffer size=", int(sizeX * self.patchSize.x),
                   "x", int(sizeY * self.patchSize.y))

        # Create the buffer which stores the rendered lights
        self._makeRenderedLightsBuffer()

        # Create per tile storage
        self._makeLightPerTileStorage()

        # Create a buffer which computes which light affects which tile
        self._makeLightBoundsComputationBuffer(sizeX, sizeY)

        # Set inputs
        self._setLightingCuller(self.lightBoundsComputeBuff)

        # Set shaders
        self._setLightCullingShader()


    def getLightCullingBuffer(self):
        """ Returns the buffer which culls the lights """
        return self.lightBoundsComputeBuff

    def _makeLightBoundsComputationBuffer(self, w, h):
        """ Creates the buffer which precomputes the lights per tile """
        self.debug("Creating light precomputation buffer of size", w, "x", h)
        self.lightBoundsComputeBuff = RenderTarget("ComputeLightTileBounds")
        self.lightBoundsComputeBuff.setSize(w, h)

        if self.settings.enableLightPerTileDebugging:
            self.lightBoundsComputeBuff.addColorTexture()
        else:
            self.lightBoundsComputeBuff.setColorWrite(False)

        self.lightBoundsComputeBuff.prepareOffscreenBuffer()

        if self.settings.enableLightPerTileDebugging:
            colorTex = self.lightBoundsComputeBuff.getColorTexture()
            colorTex.setMinfilter(SamplerState.FTNearest)
            colorTex.setMagfilter(SamplerState.FTNearest)

        self.lightBoundsComputeBuff.setShaderInput(
                "destinationBuffer", self.lightPerTileBuffer)
        self.lightBoundsComputeBuff.setShaderInput(
                "renderedLightsBuffer", self.renderedLightsBuffer)



    def _makeLightPerTileStorage(self):
        """ Creates a texture to store the lights per tile into. Should
        get replaced with ssbos later """

        perPixelDataCount = 0
        perPixelDataCount += 16 # Counters for the light types
        
        perPixelDataCount += self.maxPerTileLights["PointLight"]
        perPixelDataCount += self.maxPerTileLights["PointLightShadow"]

        perPixelDataCount += self.maxPerTileLights["DirectionalLight"]
        perPixelDataCount += self.maxPerTileLights["DirectionalLightShadow"]
        
        perPixelDataCount += self.maxPerTileLights["SpotLight"]
        perPixelDataCount += self.maxPerTileLights["SpotLightShadow"]

        self.tileStride = perPixelDataCount

        self.debug("Per pixel data:", perPixelDataCount)

        tileBufferSize = self.precomputeSize.x * self.precomputeSize.y * self.tileStride

        self.lightPerTileBuffer = Texture("LightsPerTileBuffer")
        self.lightPerTileBuffer.setupBufferTexture(
            tileBufferSize, Texture.TInt, Texture.FR32i, GeomEnums.UHDynamic)

        MemoryMonitor.addTexture("Light Per Tile Buffer", self.lightPerTileBuffer)


    def _makeRenderedLightsBuffer(self):
        """ Creates the buffer which stores the indices of all rendered lights """

        bufferSize = 16
        bufferSize += self.maxLights["PointLight"]
        bufferSize += self.maxLights["PointLightShadow"]
        bufferSize += self.maxLights["DirectionalLight"]
        bufferSize += self.maxLights["DirectionalLightShadow"]
        bufferSize += self.maxLights["SpotLight"]
        bufferSize += self.maxLights["SpotLightShadow"]

        self.renderedLightsBuffer = Texture("RenderedLightsBuffer")
        self.renderedLightsBuffer.setupBufferTexture(bufferSize, Texture.TInt, Texture.FR32i, GeomEnums.UHDynamic)

        MemoryMonitor.addTexture("Rendered Lights Buffer", self.renderedLightsBuffer)

    def addShaderDefines(self, defineList):
        """ Adds settings like the maximum light count to the list of defines
        which are available in the shader later """
        define = lambda name, val: defineList.append((name, val))

        define("MAX_VISIBLE_LIGHTS", self.maxTotalLights)

        define("MAX_POINT_LIGHTS", self.maxLights["PointLight"])
        define("MAX_SHADOWED_POINT_LIGHTS", self.maxLights["PointLightShadow"])

        define("MAX_DIRECTIONAL_LIGHTS", self.maxLights["DirectionalLight"])
        define("MAX_SHADOWED_DIRECTIONAL_LIGHTS", self.maxLights["DirectionalLightShadow"])

        define("MAX_SPOT_LIGHTS", self.maxLights["SpotLight"])
        define("MAX_SHADOWED_SPOT_LIGHTS", self.maxLights["SpotLightShadow"])

        define("MAX_TILE_POINT_LIGHTS", self.maxPerTileLights["PointLight"])
        define("MAX_TILE_SHADOWED_POINT_LIGHTS", self.maxPerTileLights["PointLightShadow"])

        define("MAX_TILE_DIRECTIONAL_LIGHTS", self.maxPerTileLights["DirectionalLight"])
        define("MAX_TILE_SHADOWED_DIRECTIONAL_LIGHTS", self.maxPerTileLights["DirectionalLightShadow"])

        define("MAX_TILE_SPOT_LIGHTS", self.maxPerTileLights["SpotLight"])
        define("MAX_TILE_SHADOWED_SPOT_LIGHTS", self.maxPerTileLights["SpotLightShadow"])

        define("SHADOW_MAX_TOTAL_MAPS", self.maxShadowMaps)
        define("LIGHTING_PER_TILE_STRIDE", self.tileStride)


    def _createShadowComputationBuffer(self):
        """ This creates the internal shadow buffer which also is the
        shadow atlas. Shadow maps are rendered to this using Viewports
        (thank you rdb for adding this!). It also setups the base camera
        which renders the shadow objects, although a custom mvp is passed
        to the shaders, so the camera is mainly a dummy """

        # Create camera showing the whole scene
        self.shadowComputeCamera = Camera("ShadowComputeCamera")
        self.shadowComputeCameraNode = self.shadowScene.attachNewNode(
            self.shadowComputeCamera)
        self.shadowComputeCamera.getLens().setFov(30, 30)
        self.shadowComputeCamera.getLens().setNearFar(1.0, 2.0)

        # Disable culling
        self.shadowComputeCamera.setBounds(OmniBoundingVolume())
        self.shadowComputeCamera.setCullBounds(OmniBoundingVolume())
        self.shadowComputeCamera.setFinal(True)
        self.shadowComputeCameraNode.setPos(0, 0, 1500)
        self.shadowComputeCameraNode.lookAt(0, 0, 0)

        self.shadowComputeTarget = RenderTarget("ShadowAtlas")
        self.shadowComputeTarget.setSize(self.shadowAtlas.getSize())
        self.shadowComputeTarget.addDepthTexture()
        self.shadowComputeTarget.setDepthBits(32)
        # self.shadowComputeTarget.setColorWrite(False)

        self.shadowComputeTarget.setSource(
            self.shadowComputeCameraNode, Globals.base.win)

        self.shadowComputeTarget.prepareSceneRender()

        # This took me a long time to figure out. If not removing the quad
        # children, the color and aux buffers will be overridden each frame.
        # Quite annoying!
        self.shadowComputeTarget.getQuad().node().removeAllChildren()
        self.shadowComputeTarget.getInternalRegion().setSort(-200)

        self.shadowComputeTarget.getInternalRegion().setNumRegions(
            self.maxShadowUpdatesPerFrame + 1)
        self.shadowComputeTarget.getInternalRegion().setDimensions(0,
             (0, 0, 0, 0))

        self.shadowComputeTarget.getInternalRegion().disableClears()
        self.shadowComputeTarget.getInternalBuffer().disableClears()
        self.shadowComputeTarget.getInternalBuffer().setSort(-300)

        # We can't clear the depth per viewport.
        # But we need to clear it in any way, as we still want
        # z-testing in the buffers. So well, we create a
        # display region *below* (smaller sort value) each viewport
        # which has a depth-clear assigned. This is hacky, I know.
        self.depthClearer = []

        for i in range(self.maxShadowUpdatesPerFrame):
            buff = self.shadowComputeTarget.getInternalBuffer()
            dr = buff.makeDisplayRegion()
            dr.setSort(-250)
            for k in xrange(16):
                dr.setClearActive(k, True)
                dr.setClearValue(k, Vec4(0.5,0.5,0.5,1))

            dr.setClearDepthActive(True)
            dr.setClearDepth(1.0)
            dr.setDimensions(0,0,0,0)
            dr.setActive(False)
            self.depthClearer.append(dr)

        # When using hardware pcf, set the correct filter types
        
        if self.settings.useHardwarePCF:
            self.pcfSampleState = SamplerState()
            self.pcfSampleState.setMinfilter(SamplerState.FTShadow)
            self.pcfSampleState.setMagfilter(SamplerState.FTShadow)
            self.pcfSampleState.setWrapU(SamplerState.WMClamp)
            self.pcfSampleState.setWrapV(SamplerState.WMClamp)


        dTex = self.getAtlasTex()
        dTex.setWrapU(Texture.WMClamp)
        dTex.setWrapV(Texture.WMClamp)

    def getAllLights(self):
        """ Returns all attached lights """
        return self.lights

    def getPCFSampleState(self):
        """ Returns the pcf sample state used to sample the shadow map """
        return self.pcfSampleState

    def processCallbacks(self):
        """ Processes all updates from the previous frame """
        for update in self.updateCallbacks:
            update.onUpdated()
        self.updateCallbacks = []

    def _createDebugTexts(self):
        """ Creates a debug overlay if specified in the pipeline settings """
        self.lightsVisibleDebugText = None
        self.lightsUpdatedDebugText = None

        if self.settings.displayDebugStats:

            try:
                from Code.GUI.FastText import FastText
                self.lightsVisibleDebugText = FastText(pos=Vec2(
                    Globals.base.getAspectRatio() - 0.1, 0.84), rightAligned=True, color=Vec3(1, 1, 0), size=0.036)
                self.lightsUpdatedDebugText = FastText(pos=Vec2(
                    Globals.base.getAspectRatio() - 0.1, 0.8), rightAligned=True, color=Vec3(1, 1, 0), size=0.036)

            except Exception, msg:
                self.debug(
                    "Overlay is disabled because FastText wasn't loaded")

    def setLightingComputator(self, shaderNode):
        """ Sets the render target which recieves the shaderinputs necessary to 
        compute the final lighting result """
        self.debug("Light computator is", shaderNode)
        self.lightingComputator = shaderNode
        self.allLightsArray.bindTo(shaderNode, "lights")
        self.allShadowsArray.bindTo(shaderNode, "shadowSources")

    def _setLightingCuller(self, shaderNode):
        """ Sets the render target which recieves the shaderinputs necessary to 
        cull the lights and pass the result to the lighting computator"""
        self.debug("Light culler is", shaderNode)
        self.lightCuller = shaderNode
        self.allLightsArray.bindTo(shaderNode, "lights")

    def getAtlasTex(self):
        """ Returns the shadow map atlas texture"""
        return self.shadowComputeTarget.getDepthTexture()

    def _queueShadowUpdate(self, source):
        """ Internal method to add a shadowSource to the list of queued updates """
        if source not in self.queuedShadowUpdates:
            self.queuedShadowUpdates.append(source)

    def addLight(self, light):
        """ Adds a light to the list of rendered lights.

        NOTICE: You have to set relevant properties like wheter the light
        casts shadows or the shadowmap resolution before calling this! 
        Otherwise it won't work (and maybe crash? I didn't test, 
        just DON'T DO IT!) """
        
        if light.attached:
            self.warn("Light is already attached!")
            return

        light.attached = True
        self.lights.append(light)

        if light.hasShadows() and not self.settings.renderShadows:
            self.warn("Attached shadow light but shadowing is disabled in pipeline.ini")
            light.setCastsShadows(False)


        sources = light.getShadowSources()

        # Check each shadow source
        for index, source in enumerate(sources):

            # Check for correct resolution
            tileSize = self.shadowAtlas.getTileSize()
            if source.resolution < tileSize or source.resolution % tileSize != 0:
                self.warn(
                    "The ShadowSource resolution has to be a multiple of the tile size (" + str(tileSize) + ")!")
                self.warn("Adjusting resolution to", tileSize)
                source.resolution = tileSize

            if source.resolution > self.shadowAtlas.getSize():
                self.warn(
                    "The ShadowSource resolution cannot be bigger than the atlas size (" + str(self.shadowAtlas.getSize()) + ")")
                self.warn("Adjusting resolution to", tileSize)
                source.resolution = tileSize

            if source not in self.shadowSources:
                self.shadowSources.append(source)

            source.setSourceIndex(self.shadowSources.index(source))
            light.setSourceIndex(index, source.getSourceIndex())

        index = self.lights.index(light)
        self.allLightsArray[index] = light

        light.queueUpdate()
        light.queueShadowUpdate()

    def removeLight(self):
        """ Removes a light. TODO """
        raise NotImplementedError()

    def reloadShader(self):
        """ Reloads all shaders. This also updates the camera state """
        self._createTagStates()
        self._setLightCullingShader()

    def setCullBounds(self, bounds):
        """ Sets the current camera bounds used for light culling """
        self.cullBounds = bounds

    def writeRenderedLightsToBuffer(self):
        """ Stores the list of rendered lights in the buffer to access it in
        the shader later """

        pstats_WriteBuffers.start()

        image = memoryview(self.renderedLightsBuffer.modifyRamImage())

        bufferEntrySize = 4

        # Write counters
        offset = 0
        image[offset:offset + bufferEntrySize * 6] = struct.pack('i' * 6, 
            len(self.renderedLights["PointLight"]),
            len(self.renderedLights["PointLightShadow"]),
            len(self.renderedLights["DirectionalLight"]),
            len(self.renderedLights["DirectionalLightShadow"]),
            len(self.renderedLights["SpotLight"]),
            len(self.renderedLights["SpotLightShadow"]))

        offset = 16 * bufferEntrySize


        # Write light lists
        for lightType in ["PointLight", "PointLightShadow", "DirectionalLight", 
            "DirectionalLightShadow", "SpotLight", "SpotLightShadow"]:
        
            entryCount = len(self.renderedLights[lightType])

            if entryCount > self.maxLights[lightType]:
                self.error("Out of lights bounds for", lightType)

            if entryCount > 0:
                # We can write all lights at once, thats pretty cool!
                image[offset:offset + entryCount * bufferEntrySize] = struct.pack('i' * entryCount, *self.renderedLights[lightType])
            offset += self.maxLights[lightType] * bufferEntrySize

        pstats_WriteBuffers.stop()

    def updateLights(self):
        """ This is one of the two per-frame-tasks. See class description
        to see what it does """

        pstats_ProcessLights.start()

        # Clear dictionary to store the lights rendered this frame
        self.renderedLights = {}

        for lightType in self.maxLights:
            self.renderedLights[lightType] = []

        # Process each light
        for index, light in enumerate(self.lights):

            # When shadow maps should be always updated
            if self.settings.alwaysUpdateAllShadows:
                light.queueShadowUpdate()

            # Update light if required
            pstats_PerLightUpdates.start()
            if light.needsUpdate():
                light.performUpdate()
            pstats_PerLightUpdates.stop()

            # Perform culling

            pstats_CullLights.start()
            if not self.cullBounds.contains(light.getBounds()):
                continue
            pstats_CullLights.stop()

            # Queue shadow updates if necessary
            if light.hasShadows() and light.needsShadowUpdate():
                neededUpdates = light.performShadowUpdate()
                for update in neededUpdates:
                    self._queueShadowUpdate(update)

            # Add light to the correct list now
            lightTypeName = light.getTypeName()
            if light.hasShadows():
                lightTypeName += "Shadow"
            self.renderedLights[lightTypeName].append(index)

        pstats_ProcessLights.stop()

        self.writeRenderedLightsToBuffer()


        # Generate debug text
        if self.lightsVisibleDebugText is not None:
            renderedPL = str(len(self.renderedLights["PointLight"]))
            renderedPL_S = str(len(self.renderedLights["PointLightShadow"]))

            renderedDL = str(len(self.renderedLights["DirectionalLight"]))
            renderedDL_S = str(len(self.renderedLights["DirectionalLightShadow"]))

            renderedSL = str(len(self.renderedLights["SpotLight"]))
            renderedSL_S = str(len(self.renderedLights["SpotLight"]))

            self.lightsVisibleDebugText.setText(
                "Point: " + renderedPL + "/" + renderedPL_S + ", Directional: " + renderedDL + "/"+  renderedDL_S + ", Spot: " + renderedSL+ "/" + renderedSL_S)


    def updateShadows(self):
        """ This is one of the two per-frame-tasks. See class description
        to see what it does """

        # First, disable all clearers
        for clearer in self.depthClearer:
            clearer.setActive(False)

        if self.skip > 0:
            self.shadowComputeTarget.setActive(False)
            self.numShadowUpdatesPTA[0] = 0
            self.skip -= 1
            return

        self.skip = self.skipRate

        # Process shadows
        queuedUpdateLen = len(self.queuedShadowUpdates)

        # Compute shadow updates
        numUpdates = 0
        last = "[ "


        # When there are no updates, disable the buffer
        if len(self.queuedShadowUpdates) < 1:
            self.shadowComputeTarget.setActive(False)
            self.numShadowUpdatesPTA[0] = 0

        else:

            # Otherwise enable the buffer
            self.shadowComputeTarget.setActive(True)

            # Check each update in the queue
            for index, update in enumerate(self.queuedShadowUpdates):

                # We only process a limited number of shadow maps
                if numUpdates >= self.maxShadowUpdatesPerFrame:
                    break

                updateSize = update.getResolution()

                # assign position in atlas if not done yet
                if not update.hasAtlasPos():

                    storePos = self.shadowAtlas.reserveTiles(
                        updateSize, updateSize, update.getUid())

                    if not storePos:

                        # No space found, try to reduce resolution
                        self.warn(
                            "Could not find space for the shadow map of size", updateSize)
                        self.warn(
                            "The size will be reduced to", self.shadowAtlas.getTileSize())

                        updateSize = self.shadowAtlas.getTileSize()
                        update.setResolution(updateSize)
                        storePos = self.shadowAtlas.reserveTiles(
                            updateSize, updateSize, update.getUid())

                        if not storePos:
                            self.fatal(
                                "Still could not find a shadow atlas position, "
                                "the shadow atlas is completely full. "
                                "Either we reduce the resolution of existing shadow maps, "
                                "increase the shadow atlas resolution, "
                                "or crash the app. Guess what I decided to do :-P")

                    update.assignAtlasPos(*storePos)

                update.update()

                # Store update in array
                indexInArray = self.shadowSources.index(update)
                self.allShadowsArray[indexInArray] = update
                self.updateShadowsArray[index] = update

                # Compute viewport & set depth clearer
                texScale = float(update.getResolution()) / \
                    float(self.shadowAtlas.getSize())

                atlasPos = update.getAtlasPos()
                left, right = atlasPos.x, (atlasPos.x + texScale)
                bottom, top = atlasPos.y, (atlasPos.y + texScale)
                self.depthClearer[numUpdates].setDimensions(
                    left, right, bottom, top)
                self.depthClearer[numUpdates].setActive(True)

                self.shadowComputeTarget.getInternalRegion().setDimensions(
                    numUpdates+1, (atlasPos.x, atlasPos.x + texScale,
                                     atlasPos.y, atlasPos.y + texScale))
                numUpdates += 1

                # Finally, we can tell the update it's valid now.
                update.setValid()

                # In the next frame the update is processed, so call it later
                self.updateCallbacks.append(update)

                # Only add the uid to the output if the max updates
                # aren't too much. Otherwise we spam the screen
                if self.maxShadowUpdatesPerFrame <= 8:
                    last += str(update.getUid()) + " "

            # Remove all updates which got processed from the list
            for i in range(numUpdates):
                self.queuedShadowUpdates.remove(self.queuedShadowUpdates[0])

            self.numShadowUpdatesPTA[0] = numUpdates

        last += "]"

        # Generate debug text
        if self.lightsUpdatedDebugText is not None:
            self.lightsUpdatedDebugText.setText(
                'Updates: ' + str(numUpdates) + "/" + str(queuedUpdateLen) + "/" + str(len(self.shadowSources)) + ", Last: " + last + ", Free Tiles: " + str(self.shadowAtlas.getFreeTileCount()) + "/" + str(self.shadowAtlas.getTotalTileCount()))

    # Main update
    def update(self):
        self.updateLights()
        self.updateShadows()
