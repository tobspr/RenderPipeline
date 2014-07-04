
from DebugObject import DebugObject
from panda3d.core import Texture, Camera, Vec3, Vec2, NodePath, PTAMat4

from BetterShader import BetterShader
from RenderTarget import RenderTarget
from RenderTargetType import RenderTargetType
from ShaderStructArray import ShaderStructArray
from Light import Light

class LightManager(DebugObject):

    def __init__(self):
        DebugObject.__init__(self, "LightManager")
        self.maxVisibleLights = 16
        self.lights = []
        self.numVisibleLights = 0
        self.cullBounds = None




        self.lightDataArray = ShaderStructArray(Light, 16)
        self.shadowScene = render

        self.maxShadowRes = 2048

        # create shadow atlas
        self.shadowAtlasSize = 2048
        self.maxShadowUpdatesPerFrame = 2

        self.shadowAtlasTex = Texture("ShadowAtlas")
        self.shadowAtlasTex.setup2dTexture(
            self.shadowAtlasSize, self.shadowAtlasSize, Texture.TFloat, Texture.FRgba8)

        self.tileSize = 128
        self.tileCount = self.shadowAtlasSize / self.tileSize
        self.tiles = []

        for i in xrange(self.tileCount):
            self.tiles.append([None for j in xrange(self.tileCount)])

        self.debug("Init shadow atlas with tileSize =",
                   self.tileSize, ", tileCount =", self.tileCount)

        # create shadow compute buffer
        self.shadowComputeCamera = Camera("ShadowComputeCamera")
        self.shadowComputeCameraNode = self.shadowScene.attachNewNode(
            self.shadowComputeCamera)
        self.shadowComputeCamera.getLens().setFov(90, 90)
        self.shadowComputeCamera.getLens().setNearFar(10.0, 10000.0)

        self.shadowComputeCameraNode.setPos(0, 0, 150)
        self.shadowComputeCameraNode.lookAt(0, 0, 0)

        self.shadowComputeTarget = RenderTarget("ShadowCompute")
        self.shadowComputeTarget.setSize(self.maxShadowRes, self.maxShadowRes)
        self.shadowComputeTarget.setLayers(self.maxShadowUpdatesPerFrame)
        self.shadowComputeTarget.addRenderTexture(RenderTargetType.Depth)
        # self.shadowComputeTarget.addRenderTexture(RenderTargetType.Color)
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
        self.shadowComputeCamera.setTagState("True", initialState.getState())
        self.shadowScene.setTag("ShadowPass", "True")

        # Debug text to show how many lights are currently visible
        try:
            from FastText import FastText
            self.lightsVisibleDebugText = FastText(pos=Vec2(
                base.getAspectRatio() - 0.1, 0.9), rightAligned=True, color=Vec3(1, 0, 0), size=0.04)
            self.lightsUpdatedDebugText = FastText(pos=Vec2(
                base.getAspectRatio() - 0.1, 0.85), rightAligned=True, color=Vec3(1, 0, 0), size=0.04)

        except Exception, msg:
            self.debug("Could not load fast text:", msg)
            self.lightsVisibleDebugText = None
            self.lightsUpdatedDebugText = None

        self.computingNodes = []

        self.updateMatrices = PTAMat4.empty_array(
            self.maxShadowUpdatesPerFrame)
        self.updateData = PTAMat4.empty_array(
            self.maxShadowUpdatesPerFrame)

        for target in [self.shadowComputeTarget, self.shadowScene]:
            target.setShaderInput("numUpdates", 0)
            target.setShaderInput("updateData", self.updateData)
            target.setShaderInput("updateMatrices", self.updateMatrices)

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
        self.debug("Finding position for map of size (", w, "x", h, "), (", tileW, "x", tileH, ")")

        maxIterW = self.tileCount - tileW + 1
        maxIterH = self.tileCount - tileH + 1

        tileFound = False
        tilePos = -1, -1

        for i in xrange(0, maxIterW):
            if tileFound:
                break

            for j in xrange(0, maxIterH):
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

        return Vec2(float(tilePos[0]) / float(self.tileCount), float(tilePos[1]) / float(self.tileCount))

    def addLight(self, light):
        self.debug("Adding light", light)
        self.lights.append(light)

    def setLightingComputators(self, shaderNodes):
        self.computingNodes = shaderNodes

        for shaderNode in self.computingNodes:
            self.lightDataArray.bindTo(shaderNode, "lights")
            shaderNode.setShaderInput("lightCount", 0)

    def debugReloadShader(self):
        self._setCopyShader()

    def setCullBounds(self, bounds):
        self.cullBounds = bounds

    def update(self):
        
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


        if self.lightsVisibleDebugText is not None:
            self.lightsVisibleDebugText.setText(
                'Visible Lights: ' + str(self.numVisibleLights))

        if self.lightsUpdatedDebugText is not None:
            self.lightsUpdatedDebugText.setText(
                'Queued Updates: ' + str(len(self.queuedShadowUpdates)))

        for shaderNode in self.computingNodes:
            shaderNode.setShaderInput("lightCount", self.numVisibleLights)

        # Compute shadows
        numUpdates = 0

        if len(self.queuedShadowUpdates) < 1:
            self.shadowComputeTarget.setActive(False)
            for target in [self.shadowComputeTarget, self.shadowScene]:
                target.setShaderInput("numUpdates", 1)

        else:
            self.shadowComputeTarget.setActive(True)

            for index, update in enumerate(self.queuedShadowUpdates):
                update.setValid()
                storePos = 0, 0
                updateSize = update.getResolution()

                # already have an atlas pos
                if update.hasAtlasPos():
                    storePos = update.getAtlasPos()
                else:
                    # otherwise find one
                    storePos = self._findAndReserveShadowAtlasPosition(
                        updateSize, updateSize, update.getUid())
                    update.assignAtlasPos(*storePos)

                # pass data to shaders
                self.updateData[index] = Mat4(
                                index, updateSize, storePos[0]*self.shadowAtlasSize, storePos[1] * self.shadowAtlasSize,
                                0,0,0,0,
                                0,0,0,0,
                                0,0,0,0

                                )
                self.updateMatrices[index] = update.getMVP()

                # self.debug("UPDATE-> ", storePos[0],"/",storePos[1], "size=",updateSize, "index=",index)

                self.queuedShadowUpdates.remove(update)
                numUpdates += 1

            for target in [self.shadowComputeTarget, self.shadowScene]:
                target.setShaderInput("numUpdates", numUpdates)
