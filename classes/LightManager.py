
from DebugObject import DebugObject
from panda3d.core import Texture, Camera, Vec3, Vec2, NodePath, PTAMat4, LVecBase2i
from panda3d.core import RenderState, ColorWriteAttrib, DepthWriteAttrib

from BetterShader import BetterShader
from RenderTarget import RenderTarget
from RenderTargetType import RenderTargetType
from ShaderStructArray import ShaderStructArray
from ShadowSource import ShadowSource
from Light import Light


class LightManager(DebugObject):

    def __init__(self):
        DebugObject.__init__(self, "LightManager")

        # maximum values
        self.maxVisibleLights = 30
        self.numVisibleLights = 0
        self.maxShadowRes = 4096
        self.shadowAtlasSize = 8192
        self.maxShadowMaps = 30
        self.maxShadowUpdatesPerFrame = 4
        self.tileSize = 32
        self.tileCount = self.shadowAtlasSize / self.tileSize
        self.tiles = []

        # create arrays to store lights & shadow sources
        self.lights = []
        self.shadowSources = []
        self.lightDataArray = ShaderStructArray(Light, 16)
        self.updateShadowsArray = ShaderStructArray(
            ShadowSource, self.maxShadowUpdatesPerFrame)
        self.allShadowsArray = ShaderStructArray(
            ShadowSource, self.maxShadowMaps)

        self.cullBounds = None

        self.shadowScene = render

        self.shadowAtlasTex = Texture("ShadowAtlas")
        self.shadowAtlasTex.setup2dTexture(
            self.shadowAtlasSize, self.shadowAtlasSize, Texture.TFloat, Texture.FRg16)

        for i in xrange(self.tileCount):
            self.tiles.append([None for j in xrange(self.tileCount)])

        self.debug("Init shadow atlas with tileSize =",
                   self.tileSize, ", tileCount =", self.tileCount)

        # create shadow compute buffer
        self.shadowComputeCamera = Camera("ShadowComputeCamera")
        self.shadowComputeCameraNode = self.shadowScene.attachNewNode(
            self.shadowComputeCamera)
        self.shadowComputeCamera.getLens().setFov(90, 90)
        self.shadowComputeCamera.getLens().setNearFar(10.0, 100000.0)

        self.shadowComputeCameraNode.setPos(0, 0, 150)
        self.shadowComputeCameraNode.lookAt(0, 0, 0)

        self.shadowComputeTarget = RenderTarget("ShadowCompute")
        self.shadowComputeTarget.setSize(self.maxShadowRes, self.maxShadowRes)
        self.shadowComputeTarget.setLayers(self.maxShadowUpdatesPerFrame)
        self.shadowComputeTarget.addRenderTexture(RenderTargetType.Depth)
        self.shadowComputeTarget.setDepthBits(32)
        self.shadowComputeTarget.setSource(
            self.shadowComputeCameraNode, base.win)
        self.shadowComputeTarget.prepareSceneRender()

        self.shadowComputeTarget.getInternalRegion().setSort(3)
        self.shadowComputeTarget.getRegion().setSort(3)

        self.queuedShadowUpdates = []

        # Assign copy shader
        self._setCopyShader()
        self.shadowComputeTarget.setShaderInput("atlas", self.shadowAtlasTex)
        self.shadowComputeTarget.setShaderInput(
            "renderResult", self.shadowComputeTarget.getDepthTexture())

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

        # Debug text to show how many lights are currently visible
        try:
            from FastText2 import FastText
            self.lightsVisibleDebugText = FastText(pos=Vec2(
                base.getAspectRatio() - 0.1, 0.84), rightAligned=True, color=Vec3(1, 0, 0), size=0.036)
            self.lightsUpdatedDebugText = FastText(pos=Vec2(
                base.getAspectRatio() - 0.1, 0.8), rightAligned=True, color=Vec3(1, 0, 0), size=0.036)

        except Exception, msg:
            self.debug("Could not load fast text:", msg)
            self.lightsVisibleDebugText = None
            self.lightsUpdatedDebugText = None

        self.computingNodes = []

        for target in [self.shadowComputeTarget, self.shadowScene]:
            target.setShaderInput("numUpdates", LVecBase2i(0) )
            self.updateShadowsArray.bindTo(target, "updateSources")


       
    def getAtlasTex(self):
        return self.shadowAtlasTex

    def _setCopyShader(self):
        copyShader = BetterShader.load(
            "Shader/DefaultPostProcess.vertex", "Shader/CopyToShadowAtlas.fragment")
        self.shadowComputeTarget.setShader(copyShader)

    def _queueShadowUpdate(self, source):
        if source not in self.queuedShadowUpdates:
            self.queuedShadowUpdates.append(source)

    def _findAndReserveShadowAtlasPosition(self, w, h, idx):

        tileW, tileH = w / self.tileSize, h / self.tileSize
        self.debug(
            "Finding position for map of size (", w, "x", h, "), (", tileW, "x", tileH, ")")

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
                "Tile found at", tilePos[0], "/", tilePos[1], "reserving for", idx)

            # *reserve* tile

            for x in xrange(0, tileW):
                for y in xrange(0, tileH):
                    self.tiles[y + tilePos[1]][x + tilePos[0]] = idx

        else:
            self.error("No free tile found! Have to update whole atlas maybe?")

            return Vec2(-1000, -1000)

        return Vec2(float(tilePos[0]) / float(self.tileCount), float(tilePos[1]) / float(self.tileCount))

    def addLight(self, light):
        self.debug("Adding light", light)
        self.lights.append(light)

        sources = light.getShadowSources()
        for index, source in enumerate(sources):
            if source not in self.shadowSources:
                self.shadowSources.append(source)


            source.setSourceIndex(self.shadowSources.index(source))

            light.setSourceIndex(index, source.getSourceIndex())

    def setLightingComputators(self, shaderNodes):
        self.computingNodes = shaderNodes

        for shaderNode in self.computingNodes:
            self.lightDataArray.bindTo(shaderNode, "lights")
            shaderNode.setShaderInput("lightCount", LVecBase2i(0) )
            self.allShadowsArray.bindTo(shaderNode, "shadowSources")


    def debugReloadShader(self):
        self._setCopyShader()

    def setCullBounds(self, bounds):
        self.cullBounds = bounds

    def update(self):

        # return

        self.numVisibleLights = 0

        for index, light in enumerate(self.lights):

            if self.numVisibleLights >= self.maxVisibleLights:
                # too many lights
                self.error(
                    "Too many lights! Can't display more than", self.maxVisibleLights)
                break

            # update light if required
            if light.needsUpdate():
                light.performUpdate()

            # check if visible
            if not self.cullBounds.contains(light.getBounds()):
                continue

            if light.needsShadowUpdate():
                neededUpdates = light.performShadowUpdate()

                for update in neededUpdates:
                    self._queueShadowUpdate(update)

            # todo: visibility check
            self.lightDataArray[self.numVisibleLights] = light
            self.numVisibleLights += 1

        queuedUpdateLen = int(len(self.queuedShadowUpdates))

        for shaderNode in self.computingNodes:
            shaderNode.setShaderInput("lightCount", LVecBase2i(self.numVisibleLights) )

        # Compute shadow updates
        numUpdates = 0
        last = "[ "

        if len(self.queuedShadowUpdates) < 1:
            self.shadowComputeTarget.setActive(False)
            for target in [self.shadowComputeTarget, self.shadowScene]:
                target.setShaderInput("numUpdates", LVecBase2i(0) )
                pass

        else:
            self.shadowComputeTarget.setActive(True)

            for index, update in enumerate(self.queuedShadowUpdates):
                if numUpdates >= self.maxShadowUpdatesPerFrame:
                    # print "Skip:", update
                    break

                update.setValid()
                updateSize = update.getResolution()

                # assign position in atlas if necessary
                if not update.hasAtlasPos():
                    storePos = self._findAndReserveShadowAtlasPosition(
                        updateSize, updateSize, update.getUid())
                    update.assignAtlasPos(*storePos)


                update.update()


                indexInArray = self.shadowSources.index(update)
                self.allShadowsArray[indexInArray] = update

                self.updateShadowsArray[index] = update
                # self.queuedShadowUpdates.remove(update)
                numUpdates += 1

                last += str(update.getUid()) + " "


            for i in xrange(numUpdates):
                self.queuedShadowUpdates.remove(self.queuedShadowUpdates[0])

            for target in [self.shadowComputeTarget, self.shadowScene]:
                target.setShaderInput("numUpdates", LVecBase2i(numUpdates) )
                pass


        last += "]"

        if self.lightsVisibleDebugText is not None:
            self.lightsVisibleDebugText.setText(
                'Visible Lights: ' + str(self.numVisibleLights) + "/" + str(len(self.lights)))

        if self.lightsUpdatedDebugText is not None:
            self.lightsUpdatedDebugText.setText(
                'Queued Updates: ' + str(numUpdates) + "/" + str(queuedUpdateLen) + "/" + str(len(self.shadowSources)) + ", Last: " + last)
