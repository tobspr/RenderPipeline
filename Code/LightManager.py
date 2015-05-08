
import math
import struct

from panda3d.core import Texture, Camera, Vec3, Vec2, NodePath, RenderState
from panda3d.core import Shader, GeomEnums, MatrixLens
from panda3d.core import CullFaceAttrib, ColorWriteAttrib, DepthWriteAttrib
from panda3d.core import OmniBoundingVolume, PTAInt, Vec4, PTAVecBase4f
from panda3d.core import LVecBase2i, ShaderAttrib, UnalignedLVecBase4f
from panda3d.core import ComputeNode, LVecBase4i, GraphicsOutput, SamplerState
from panda3d.core import PStatCollector
from panda3d.core import Shader, Filename

from Light import Light
from DebugObject import DebugObject
from RenderTarget import RenderTarget
from ShadowSource import ShadowSource
from ShadowAtlas import ShadowAtlas
from ShaderStructArray import ShaderStructArray
from Globals import Globals
from MemoryMonitor import MemoryMonitor
from LightLimits import LightLimits


from Code.RenderPasses.ShadowScenePass import ShadowScenePass
from Code.RenderPasses.LightCullingPass import LightCullingPass

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

        self.renderedLights = {}
        self.pipeline = pipeline

        # Create arrays to store lights & shadow sources
        self.lights = []
        self.shadowSources = []
        self.queuedShadowUpdates = []
        self.allLightsArray = ShaderStructArray(Light, LightLimits.maxTotalLights)
        self.updateCallbacks = []

        self.cullBounds = None
        self.shadowScene = Globals.render

        # Create atlas
        self.shadowAtlas = ShadowAtlas()
        self.shadowAtlas.setSize(self.pipeline.settings.shadowAtlasSize)
        self.shadowAtlas.create()

        self.maxShadowUpdatesPerFrame = self.pipeline.settings.maxShadowUpdatesPerFrame
        self.numShadowUpdatesPTA = PTAInt.emptyArray(1)

        self.updateShadowsArray = ShaderStructArray(
            ShadowSource, self.maxShadowUpdatesPerFrame)
        self.allShadowsArray = ShaderStructArray(
            ShadowSource, LightLimits.maxShadowMaps)

        # Create shadow compute buffer
        self._createShadowPass()
        self._initLightCulling()

        # Create the initial shadow state
        self.shadowScene.setTag("ShadowPassShader", "Default")

        # Register variables & arrays
        self.pipeline.getRenderPassManager().registerDynamicVariable("shadowUpdateSources", 
            self._bindUpdateSources)
        self.pipeline.getRenderPassManager().registerDynamicVariable("allLights", 
            self._bindAllLights)
        self.pipeline.getRenderPassManager().registerDynamicVariable("allShadowSources", 
            self._bindAllSources)

        self.pipeline.getRenderPassManager().registerStaticVariable("numShadowUpdates", 
            self.numShadowUpdatesPTA)

        self.addShaderDefines()
        self.lightingComputator = None
        self._createDebugTexts()

    def _bindUpdateSources(self, renderPass, name):
        """ Internal method to bind the shadow update source to a target """
        self.updateShadowsArray.bindTo(renderPass, name)

    def _bindAllLights(self, renderPass, name):
        """ Internal method to bind the global lights array to a target """
        self.allLightsArray.bindTo(renderPass, name)

    def _bindAllSources(self, renderPass, name):
        """ Internal method to bind the global shadow sources to a target """
        self.allShadowsArray.bindTo(renderPass, name)

    def _createShadowPass(self):
        """ Creates the shadow pass, where the shadow atlas is generated into """
        self.shadowPass = ShadowScenePass()
        self.shadowPass.setMaxRegions(self.maxShadowUpdatesPerFrame)
        self.shadowPass.setSize(self.shadowAtlas.getSize())
        self.pipeline.getRenderPassManager().registerPass(self.shadowPass)

    def _initLightCulling(self):
        """ Creates the pass which gets a list of lights and computes which
        light affects which tile """

        # Fetch patch size
        self.patchSize = LVecBase2i(
            self.pipeline.settings.computePatchSizeX,
            self.pipeline.settings.computePatchSizeY)

        # size has to be a multiple of the compute unit size
        # but still has to cover the whole screen
        sizeX = int(math.ceil(float(self.pipeline.getSize().x) / self.patchSize.x))
        sizeY = int(math.ceil(float(self.pipeline.getSize().y) / self.patchSize.y))

        self.lightCullingPass = LightCullingPass()
        self.lightCullingPass.setSize(sizeX, sizeY)
        self.lightCullingPass.setPatchSize(self.patchSize.x, self.patchSize.y)

        self.pipeline.getRenderPassManager().registerPass(self.lightCullingPass)
        self.pipeline.getRenderPassManager().registerStaticVariable("lightingTileCount", LVecBase2i(sizeX, sizeY))

        self.debug("Batch size =", sizeX, "x", sizeY,
                   "Actual Buffer size=", int(sizeX * self.patchSize.x),
                   "x", int(sizeY * self.patchSize.y))

        # Create the buffer which stores the rendered lights
        self._makeRenderedLightsBuffer()

    def _makeRenderedLightsBuffer(self):
        """ Creates the buffer which stores the indices of all rendered lights """

        bufferSize = 16
        bufferSize += LightLimits.maxLights["PointLight"]
        bufferSize += LightLimits.maxLights["PointLightShadow"]
        bufferSize += LightLimits.maxLights["DirectionalLight"]
        bufferSize += LightLimits.maxLights["DirectionalLightShadow"]
        bufferSize += LightLimits.maxLights["SpotLight"]
        bufferSize += LightLimits.maxLights["SpotLightShadow"]

        self.renderedLightsBuffer = Texture("RenderedLightsBuffer")
        self.renderedLightsBuffer.setupBufferTexture(bufferSize, Texture.TInt, Texture.FR32i, GeomEnums.UHDynamic)

        self.pipeline.getRenderPassManager().registerStaticVariable(
            "renderedLightsBuffer", self.renderedLightsBuffer)

        MemoryMonitor.addTexture("Rendered Lights Buffer", self.renderedLightsBuffer)

    def addShaderDefines(self):
        """ Adds settings like the maximum light count to the list of defines
        which are available in the shader later """
        define = lambda name, val: self.pipeline.getRenderPassManager().registerDefine(name, val)
        settings = self.pipeline.settings


        define("MAX_VISIBLE_LIGHTS", LightLimits.maxTotalLights)

        define("MAX_POINT_LIGHTS", LightLimits.maxLights["PointLight"])
        define("MAX_SHADOWED_POINT_LIGHTS", LightLimits.maxLights["PointLightShadow"])

        define("MAX_DIRECTIONAL_LIGHTS", LightLimits.maxLights["DirectionalLight"])
        define("MAX_SHADOWED_DIRECTIONAL_LIGHTS", LightLimits.maxLights["DirectionalLightShadow"])

        define("MAX_SPOT_LIGHTS", LightLimits.maxLights["SpotLight"])
        define("MAX_SHADOWED_SPOT_LIGHTS", LightLimits.maxLights["SpotLightShadow"])

        define("MAX_TILE_POINT_LIGHTS", LightLimits.maxPerTileLights["PointLight"])
        define("MAX_TILE_SHADOWED_POINT_LIGHTS", LightLimits.maxPerTileLights["PointLightShadow"])

        define("MAX_TILE_DIRECTIONAL_LIGHTS", LightLimits.maxPerTileLights["DirectionalLight"])
        define("MAX_TILE_SHADOWED_DIRECTIONAL_LIGHTS", LightLimits.maxPerTileLights["DirectionalLightShadow"])

        define("MAX_TILE_SPOT_LIGHTS", LightLimits.maxPerTileLights["SpotLight"])
        define("MAX_TILE_SHADOWED_SPOT_LIGHTS", LightLimits.maxPerTileLights["SpotLightShadow"])

        define("SHADOW_MAX_TOTAL_MAPS", LightLimits.maxShadowMaps)


        define("LIGHTING_COMPUTE_PATCH_SIZE_X", settings.computePatchSizeX)
        define("LIGHTING_COMPUTE_PATCH_SIZE_Y", settings.computePatchSizeY)
        define("LIGHTING_MIN_MAX_DEPTH_ACCURACY", settings.minMaxDepthAccuracy)

        if settings.useSimpleLighting:
            define("USE_SIMPLE_LIGHTING", 1)

        if settings.anyLightBoundCheck:
            define("LIGHTING_ANY_BOUND_CHECK", 1)

        if settings.accurateLightBoundCheck:
            define("LIGHTING_ACCURATE_BOUND_CHECK", 1)

        if settings.renderShadows:
            define("USE_SHADOWS", 1)

        if settings.enableLightPerTileDebugging:
            define("ENABLE_LIGHT_PER_TILE_DEBUG", 1)

        define("AMBIENT_CUBEMAP_SAMPLES", settings.ambientCubemapSamples)
        define("SHADOW_MAP_ATLAS_SIZE", settings.shadowAtlasSize)
        define("SHADOW_MAX_UPDATES_PER_FRAME", settings.maxShadowUpdatesPerFrame)
        define("SHADOW_GEOMETRY_MAX_VERTICES", settings.maxShadowUpdatesPerFrame * 3)
        define("CUBEMAP_ANTIALIASING_FACTOR", settings.cubemapAntialiasingFactor)
        define("SHADOW_NUM_PCF_SAMPLES", settings.numPCFSamples)

        if settings.usePCSS:
            define("USE_PCSS", 1)

        define("SHADOW_NUM_PCSS_SEARCH_SAMPLES", settings.numPCSSSearchSamples)
        define("SHADOW_NUM_PCSS_FILTER_SAMPLES", settings.numPCSSFilterSamples)
        define("SHADOW_PSSM_BORDER_PERCENTAGE", settings.shadowCascadeBorderPercentage)

        if settings.useHardwarePCF:
            define("USE_HARDWARE_PCF", 1)

    def processCallbacks(self):
        """ Processes all updates from the previous frame """
        for update in self.updateCallbacks:
            update.onUpdated()
        self.updateCallbacks = []

    def _createDebugTexts(self):
        """ Creates a debug overlay if specified in the pipeline settings """
        self.lightsVisibleDebugText = None
        self.lightsUpdatedDebugText = None

        if self.pipeline.settings.displayDebugStats:
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

        if light.hasShadows() and not self.pipeline.settings.renderShadows:
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

            if entryCount > LightLimits.maxLights[lightType]:
                self.error("Out of lights bounds for", lightType)

            if entryCount > 0:
                # We can write all lights at once, thats pretty cool!
                image[offset:offset + entryCount * bufferEntrySize] = struct.pack('i' * entryCount, *self.renderedLights[lightType])
            offset += LightLimits.maxLights[lightType] * bufferEntrySize

        pstats_WriteBuffers.stop()

    def updateLights(self):
        """ This is one of the two per-frame-tasks. See class description
        to see what it does """

        pstats_ProcessLights.start()

        # Clear dictionary to store the lights rendered this frame
        self.renderedLights = {}

        for lightType in LightLimits.maxLights:
            self.renderedLights[lightType] = []

        # Process each light
        for index, light in enumerate(self.lights):

            # When shadow maps should be always updated
            if self.pipeline.settings.alwaysUpdateAllShadows:
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

        # Process shadows
        queuedUpdateLen = len(self.queuedShadowUpdates)

        # Compute shadow updates
        numUpdates = 0
        last = "[ "

        # When there are no updates, disable the buffer
        if len(self.queuedShadowUpdates) < 1:
            self.shadowPass.setActiveRegionCount(0)
            self.numShadowUpdatesPTA[0] = 0

        else:

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

                self.shadowPass.setRegionDimensions(numUpdates, left, right, bottom, top)
                regionCam = self.shadowPass.getRegionCamera(numUpdates)
                regionCam.setPos(update.cameraNode.getPos())
                regionCam.setHpr(update.cameraNode.getHpr())
                regionCam.node().setLens(update.getLens())

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

            self.shadowPass.setActiveRegionCount(numUpdates)

        last += "]"

        # Generate debug text
        if self.lightsUpdatedDebugText is not None:
            self.lightsUpdatedDebugText.setText(
                'Updates: ' + str(numUpdates) + "/" + str(queuedUpdateLen) + "/" + str(len(self.shadowSources)) + ", Last: " + last + ", Free Tiles: " + str(self.shadowAtlas.getFreeTileCount()) + "/" + str(self.shadowAtlas.getTotalTileCount()))

    # Main update
    def update(self):
        self.updateLights()
        self.updateShadows()
