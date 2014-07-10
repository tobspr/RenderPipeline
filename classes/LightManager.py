
from DebugObject import DebugObject
from panda3d.core import Texture, Camera, Vec3, Vec2, NodePath, PTAMat4, LVecBase2i
from panda3d.core import RenderState, ColorWriteAttrib, DepthWriteAttrib, PTAInt, PTALVecBase4f, PTAInt

from BetterShader import BetterShader
from RenderTarget import RenderTarget
from RenderTargetType import RenderTargetType
from ShaderStructArray import ShaderStructArray
from ShadowSource import ShadowSource
from Light import Light


class LightManager(DebugObject):

    def __init__(self):
        DebugObject.__init__(self, "LightManager")

        self._initArrays()

        # create arrays to store lights & shadow sources
        self.lights = []
        self.shadowSources = []
        self.allLightsArray = ShaderStructArray(Light, 30)

        self.cullBounds = None
        self.shadowScene = render

        ## SHADOW ATLAS ##
        # todo: move to separate class

        # When you change this, change also SHADOW_MAP_ATLAS_SIZE in configuration.include,
        # and reduce the default shadow map resolution of point lights
        self.shadowAtlasSize = 8192
        self.maxShadowMaps = 24

        # When you change it , change also SHAODOW_GEOMETRY_MAX_VERTICES and
        # SHADOW_MAX_UPDATES_PER_FRAME in configuration.include!
        self.maxShadowUpdatesPerFrame = 2
        self.tileSize = 128
        self.tileCount = self.shadowAtlasSize / self.tileSize
        self.tiles = []

        self.updateShadowsArray = ShaderStructArray(
            ShadowSource, self.maxShadowUpdatesPerFrame)
        self.allShadowsArray = ShaderStructArray(
            ShadowSource, self.maxShadowMaps)


        # self.shadowAtlasTex = Texture("ShadowAtlas")
        # self.shadowAtlasTex.setup2dTexture(
        #     self.shadowAtlasSize, self.shadowAtlasSize, Texture.TFloat, Texture.FRg16)
        # self.shadowAtlasTex.setMinfilter(Texture.FTLinear)
        # self.shadowAtlasTex.setMagfilter(Texture.FTLinear)

        self.debug("Init shadow atlas with tileSize =",
                   self.tileSize, ", tileCount =", self.tileCount)

        for i in xrange(self.tileCount):
            self.tiles.append([None for j in xrange(self.tileCount)])

        # create shadow compute buffer
        self.shadowComputeCamera = Camera("ShadowComputeCamera")
        self.shadowComputeCameraNode = self.shadowScene.attachNewNode(
            self.shadowComputeCamera)
        self.shadowComputeCamera.getLens().setFov(90, 90)
        self.shadowComputeCamera.getLens().setNearFar(10.0, 100000.0)

        self.shadowComputeCameraNode.setPos(0, 0, 150)
        self.shadowComputeCameraNode.lookAt(0, 0, 0)

        self.shadowComputeTarget = RenderTarget("ShadowCompute")
        self.shadowComputeTarget.setSize(self.shadowAtlasSize, self.shadowAtlasSize)
        # self.shadowComputeTarget.setLayers(self.maxShadowUpdatesPerFrame)
        self.shadowComputeTarget.addRenderTexture(RenderTargetType.Depth)
        self.shadowComputeTarget.setDepthBits(32)
        self.shadowComputeTarget.setSource(
            self.shadowComputeCameraNode, base.win)
        self.shadowComputeTarget.prepareSceneRender()

        self.shadowComputeTarget.getInternalRegion().setSort(3)
        self.shadowComputeTarget.getRegion().setSort(3)

        self.shadowComputeTarget.getInternalRegion().setNumRegions(self.maxShadowUpdatesPerFrame + 1)
        self.shadowComputeTarget.getInternalRegion().setDimensions(0, (0,1,0,1))
        self.shadowComputeTarget.setClearDepth(False)


        self.depthClearer = []

        for i in xrange(self.maxShadowUpdatesPerFrame):
            buff = self.shadowComputeTarget.getInternalBuffer()
            dr = buff.makeDisplayRegion()
            dr.setSort(2)
            dr.setClearDepthActive(True)
            dr.setClearDepth(1.0)
            dr.setClearColorActive(False)
            dr.setDimensions(0,0,0,0)
            self.depthClearer.append(dr)




        self.queuedShadowUpdates = []

        # Assign copy shader
        self._setCopyShader()
        # self.shadowComputeTarget.setShaderInput("atlas", self.shadowComputeTarget.getColorTexture())
        # self.shadowComputeTarget.setShaderInput(
        #     "renderResult", self.shadowComputeTarget.getDepthTexture())

        # self.shadowComputeTarget.setActive(False)

        # Create shadow caster shader
        self.shadowCasterShader = BetterShader.load(
            "Shader/DefaultShadowCaster.vertex", "Shader/DefaultShadowCaster.fragment", "Shader/DefaultShadowCaster.geometry")

        self.shadowComputeCamera.setTagStateKey("ShadowPass")
        initialState = NodePath("ShadowCasterState")
        initialState.setShader(self.shadowCasterShader, 30)
        self.shadowComputeCamera.setInitialState(RenderState.make(
            ColorWriteAttrib.make(ColorWriteAttrib.C_off),
            DepthWriteAttrib.make(DepthWriteAttrib.M_on),
            100))

        self.shadowComputeCamera.setTagState("True", initialState.getState())
        self.shadowScene.setTag("ShadowPass", "True")

        self._createDebugTexts()

        self.updateShadowsArray.bindTo(self.shadowScene, "updateSources")
        self.updateShadowsArray.bindTo(self.shadowComputeTarget, "updateSources")

        self.numShadowUpdatesPTA = PTAInt.emptyArray(1)

        # Set initial inputs
        for target in [self.shadowComputeTarget, self.shadowScene]:
            target.setShaderInput("numUpdates", self.numShadowUpdatesPTA)

        self.lightingComputator = None
        self.lightCuller = None

    # Tries to create debug text to show how many lights are currently visible
    # / rendered
    def _createDebugTexts(self):
        try:
            from FastText import FastText
            self.lightsVisibleDebugText = FastText(pos=Vec2(
                base.getAspectRatio() - 0.1, 0.84), rightAligned=True, color=Vec3(1, 0, 0), size=0.036)
            self.lightsUpdatedDebugText = FastText(pos=Vec2(
                base.getAspectRatio() - 0.1, 0.8), rightAligned=True, color=Vec3(1, 0, 0), size=0.036)

        except Exception, msg:
            self.debug("Could not load fast text:", msg)
            self.debug("Overlay is disabled because FastText wasn't loaded")
            self.lightsVisibleDebugText = None
            self.lightsUpdatedDebugText = None

    # Inits the light arrays passed to the shader
    def _initArrays(self):

        # Max Visible Lights (limited because shaders can have max 1024 uniform
        # floats)

        # If you change this, don't forget to change it also in
        # Shader/Includes/Configuration.include!
        self.maxLights = {
            "PointLight": 8,
            # "DirectionalLight": 2
        }

        # Max shadow casting lights
        self.maxShadowLights = {
            "PointLight": 16,
            # "DirectionalLight": 1
        }

        for lightType, maxCount in self.maxShadowLights.items():
            self.maxLights[lightType + "Shadow"] = maxCount

        # Create array to store number of rendered lights this frame
        self.numRenderedLights = {}

        # Also create a PTAInt for every light type, which stores only the
        # light id
        self.renderedLightsArrays = {}
        for lightType, maxCount in self.maxLights.items():
            self.renderedLightsArrays[lightType] = PTAInt.emptyArray(maxCount)
            self.numRenderedLights[lightType] = PTAInt.emptyArray(1)

        for lightType, maxCount in self.maxShadowLights.items():
            self.renderedLightsArrays[
                lightType + "Shadow"] = PTAInt.emptyArray(maxCount)
            self.numRenderedLights[lightType + "Shadow"] = PTAInt.emptyArray(1)

    # Sets the render target which recieves the shaderinputs necessary to
    # Compute the final lighting result
    def setLightingComputator(self, shaderNode):
        self.debug("Light computator is", shaderNode)
        self.lightingComputator = shaderNode

        self.allLightsArray.bindTo(shaderNode, "lights")
        self.allShadowsArray.bindTo(shaderNode, "shadowSources")

        for lightType, arrayData in self.renderedLightsArrays.items():
            shaderNode.setShaderInput("array" + lightType, arrayData)
            shaderNode.setShaderInput(
                "count" + lightType, self.numRenderedLights[lightType])

        self._rebindArrays()

    # Sets the render target which recieves the shaderInputs necessary to
    # cull the lights and pass the result to the computator
    def setLightingCuller(self, shaderNode):
        self.debug("Light culler is", shaderNode)
        self.lightCuller = shaderNode

        self.allLightsArray.bindTo(shaderNode, "lights")

        # The culler needs the visible lights ids / counts as he has
        # to determine wheter a light is visible or not
        for lightType, arrayData in self.renderedLightsArrays.items():
            shaderNode.setShaderInput("array" + lightType, arrayData)
            shaderNode.setShaderInput(
                "count" + lightType, self.numRenderedLights[lightType])

        self._rebindArrays()

    def _rebindArrays(self):
        # todo: actually we only have to rebind the new items
        for index, light in enumerate(self.lights):
            self.allLightsArray[index] = light

    # Returns the shadow map atlas. You can use this for debugging
    def getAtlasTex(self):
        return self.shadowComputeTarget.getDepthTexture()

    # Assigns the copy shader which copies the rendered shadowmap to the atlas
    def _setCopyShader(self):
        # copyShader = BetterShader.load(
            # "Shader/DefaultPostProcess.vertex", "Shader/CopyToShadowAtlas.fragment")
        # self.shadowComputeTarget.setShader(copyShader)
        pass

    # Internal method to add a shadowSource to the list of queued updates
    def _queueShadowUpdate(self, source):
        if source not in self.queuedShadowUpdates:
            self.queuedShadowUpdates.append(source)

    # Finds a position in the shadow atlas for a tile. Todo: Move to a
    # seperate class
    def _findAndReserveShadowAtlasPosition(self, w, h, idx):
        tileW, tileH = w / self.tileSize, h / self.tileSize
        self.debug("Finding position for map of size (", w, "x", h, "), (", tileW, "x", tileH, ")")
        maxIterW = self.tileCount - tileW + 1
        maxIterH = self.tileCount - tileH + 1

        tileFound = False
        tilePos = -1, -1

        for j in xrange(0, maxIterW):
            if tileFound:
                break
            for i in xrange(0, maxIterH):
                if tileFound:
                    break
                tileFree = True
                # check tile starting at (i, j)
                for x in xrange(tileW):
                    for y in xrange(tileH):
                        if not tileFree:
                            break
                        if self.tiles[j + y][i + x] is not None:
                            tileFree = False
                            break
                if tileFree:
                    tileFound = True
                    tilePos = i, j
                    break

        if tileFound:
            self.debug(
                "Tile for shadowSource #"+ str(idx) + " found at", tilePos[0]*self.tileSize, "/", tilePos[1]*self.tileSize)
            for x in xrange(0, tileW):
                for y in xrange(0, tileH):
                    self.tiles[y + tilePos[1]][x + tilePos[0]] = idx
        else:
            self.error("No free tile found! Have to update whole atlas maybe?")
            return Vec2(-1000, -1000)

        return Vec2(float(tilePos[0]) / float(self.tileCount), float(tilePos[1]) / float(self.tileCount))

    # Adds a light to the list of rendered lights
    def addLight(self, light):
        self.lights.append(light)

        sources = light.getShadowSources()
        for index, source in enumerate(sources):
            if source not in self.shadowSources:
                self.shadowSources.append(source)

            source.setSourceIndex(self.shadowSources.index(source))
            light.setSourceIndex(index, source.getSourceIndex())
        light.queueUpdate()
        light.queueShadowUpdate()
        self._rebindArrays()

    # Removes a light
    def removeLight(self):
        raise NotImplementedError()

    # Reloads the shaders
    def debugReloadShader(self):
        self._setCopyShader()

    # Sets the bounds used for culling
    def setCullBounds(self, bounds):
        self.cullBounds = bounds

    # Main update
    def update(self):

        # Reset light counts
        # We don't have to reset the data-vectors, as we overwrite them
        for key in self.numRenderedLights:
            self.numRenderedLights[key][0] = 0

        # Process each light
        for index, light in enumerate(self.lights):

            # todo: check if > max lights

            # Update light if required
            if light.needsUpdate():
                light.performUpdate()
                self.allLightsArray[index] = light

            # Check if visible
            if not self.cullBounds.contains(light.getBounds()):
                continue

            # Queue shadow updates if necessary
            if light.hasShadows() and light.needsShadowUpdate():
                neededUpdates = light.performShadowUpdate()
                for update in neededUpdates:
                    self._queueShadowUpdate(update)

            lightTypeName = light.getTypeName()

            # Add to the correct list now
            if light.hasShadows():
                lightTypeName += "Shadow"

            # Add to array and increment counter
            oldCount = self.numRenderedLights[lightTypeName][0]

            if oldCount >= self.maxLights[lightTypeName]:
                self.debug("Too many lights of type", lightTypeName,
                           "-> max is", self.maxLights[lightTypeName])
                continue

            # print "Rendering light #",index, "to",lightTypeName
            # print " -> Radius:",light.radius

            arrayIndex = self.numRenderedLights[lightTypeName][0]
            self.numRenderedLights[lightTypeName][0] = oldCount + 1
            self.renderedLightsArrays[lightTypeName][arrayIndex] = index

        renderedPL = "P:" + str(self.numRenderedLights["PointLight"][0])
        renderedPL_S = "SP:" + \
            str(self.numRenderedLights["PointLightShadow"][0])

        if self.lightsVisibleDebugText is not None:
            self.lightsVisibleDebugText.setText(
                'Lights: ' + renderedPL + "/" + renderedPL_S)

        # Process shadows
        queuedUpdateLen = len(self.queuedShadowUpdates)

        # Compute shadow updates
        numUpdates = 0
        last = "[ "

        # print

        for clearer in self.depthClearer:
            clearer.setActive(False)

        # No updates
        if len(self.queuedShadowUpdates) < 1:
            # self.shadowComputeTarget.setActive(False)
            self.numShadowUpdatesPTA[0] = 0

        else:

            # self.shadowComputeTarget.setActive(True)

            # self.shadowComputeTarget.getInternalRegion().setNumRegions(self.maxShadowUpdatesPerFrame)

            for index, update in enumerate(self.queuedShadowUpdates):
                if numUpdates >= self.maxShadowUpdatesPerFrame:
                    break

                update.setValid()
                updateSize = update.getResolution()

                # assign position in atlas if not done yet
                if not update.hasAtlasPos():
                    storePos = self._findAndReserveShadowAtlasPosition(
                        updateSize, updateSize, update.getUid())
                    update.assignAtlasPos(*storePos)

                update.update()

                indexInArray = self.shadowSources.index(update)
                self.allShadowsArray[indexInArray] = update
                self.updateShadowsArray[index] = update

                texScale = float(update.getResolution()) / float(self.shadowAtlasSize)

                # print "texScale:",texScale

                atlasPos = update.getAtlasPos()

                # print
                # print
                # print
                # print
                # print numUpdates, "->",(atlasPos.x,atlasPos.x + texScale,atlasPos.y, atlasPos.y + texScale)
                left, right = atlasPos.x, (atlasPos.x + texScale)
                bottom, top = atlasPos.y, (atlasPos.y + texScale)

                # print "\t",left,right,bottom,top


                self.depthClearer[numUpdates].setDimensions(left, right, bottom, top)
                # self.depthClearer[numUpdates].setDimensions(0,1,0,1)
                self.depthClearer[numUpdates].setActive(True)

                # self.shadowComputeTarget.getInternalRegion().setDimensions(numUpdates, (atlasPos.x,atlasPos.x + texScale,atlasPos.y, atlasPos.y + texScale))
                self.shadowComputeTarget.getInternalRegion().setDimensions(numUpdates + 1, (atlasPos.x,atlasPos.x + texScale,atlasPos.y, atlasPos.y + texScale))
                numUpdates += 1

            for i in xrange(numUpdates):
                self.queuedShadowUpdates.remove(self.queuedShadowUpdates[0])

            self.numShadowUpdatesPTA[0] = numUpdates

        last += "]"



        if self.lightsUpdatedDebugText is not None:
            self.lightsUpdatedDebugText.setText(
                'Queued Updates: ' + str(numUpdates) + "/" + str(queuedUpdateLen) + "/" + str(len(self.shadowSources)) + ", Last: " + last)
