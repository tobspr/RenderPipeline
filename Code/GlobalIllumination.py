
from panda3d.core import Texture, NodePath, ShaderAttrib, Vec4, Vec3
from panda3d.core import LVecBase3i, PTAMat4
from panda3d.core import UnalignedLMatrix4f, OmniBoundingVolume

from Globals import Globals
from DebugObject import DebugObject
from BetterShader import BetterShader
from LightType import LightType
from GUI.BufferViewerGUI import BufferViewerGUI


class GlobalIllumnination(DebugObject):

    """ This class handles the global illumination processing """

    class GIStage:

        def __init__(self, size):
            self.geometryTexture = self._allocTexture(size)
            self.shRedTexture = self._allocTexture(size)
            self.shGreenTexture = self._allocTexture(size)
            self.shBlueTexture = self._allocTexture(size)

        def _allocTexture(self, size):
            tex = Texture("tex")
            tex.setup2dTexture(
                size * size, size, Texture.TFloat, Texture.FRgba16)
            return tex

    def __init__(self, pipeline):
        DebugObject.__init__(self, "GlobalIllumnination")
        self.pipeline = pipeline

    def setup(self):
        """ Setups everything for the GI to work """
        self.debug("Setup ..")

        self.cascadeSize = 64

        self.sourcesData = PTAMat4.emptyArray(24)
        self.mvpData = PTAMat4.emptyArray(24)

        self.stages = [
            self.GIStage(self.cascadeSize),
            self.GIStage(self.cascadeSize),
        ]

        self.resultStage = self.GIStage(self.cascadeSize)

        BufferViewerGUI.registerTexture(
            "GI-GeometryTexture", self.resultStage.geometryTexture)
        BufferViewerGUI.registerTexture(
            "GI-ColorTexture", self.resultStage.shRedTexture)
        # BufferViewerGUI.registerTexture("GI-Result", self.resultStorage)
        # BufferViewerGUI.registerTexture("GI-VPLStorageTemp", self.vplStorageTemp)
        # BufferViewerGUI.registerTexture("GI-ColorStorageTemp", self.colorStorageTemp)

        # self.gridStart = Vec3(-20, -20, -1)
        # self.gridEnd = Vec3(20, 20, 39)

        self.gridStart = Vec3(-80, -38, -1)
        self.gridEnd = Vec3(80, 38, 80)

        self.voxelSize = (self.gridEnd - self.gridStart) / self.cascadeSize
        self.delay = 0
        self.frameIndex = 0

        self.iterations = 64

        # Debugging of voxels
        self.debugVoxels = True

        if self.debugVoxels:
            self.createVoxelDebugBox()

        # Iterations always has to be a multiple of two, because we render
        # ping-pong
        self.iterations *= 2
        self.reloadShader()
        self._clearTexture(self.resultStorage)

    def createVoxelDebugBox(self):
        box = Globals.loader.loadModel("box")

        gridVisualizationSize = 64
        box.setScale(self.voxelSize)
        box.setPos(self.gridStart)
        box.reparentTo(Globals.base.render)
        box.setInstanceCount(
            gridVisualizationSize * gridVisualizationSize * gridVisualizationSize)
        box.node().setFinal(True)
        box.node().setBounds(OmniBoundingVolume())
        box.setShaderInput("giGrid", self.vplStorage)
        box.setShaderInput("realGridSize", self.cascadeSize)
        box.setShaderInput("giColorGrid", self.resultStorage)
        box.setShaderInput(
            "scaleFactor", self.cascadeSize / float(gridVisualizationSize))
        box.setShaderInput("effectiveGrid", int(gridVisualizationSize))
        self.box = box
        self._setBoxShader()

    def _setBoxShader(self):
        self.box.setShader(BetterShader.load(
            "Shader/GI/DebugVoxels.vertex", "Shader/GI/DebugVoxels.fragment"))

    def _createCleanShader(self):
        shader = BetterShader.loadCompute("Shader/GI/ClearTexture.compute")
        self.clearTextureNode = NodePath("ClearTexture")
        self.clearTextureNode.setShader(shader)

    def _createPopulateShader(self):
        shader = BetterShader.loadCompute("Shader/GI/PopulateVPL.compute")
        self.populateVPLNode = NodePath("PopulateVPLs")
        self.populateVPLNode.setShader(shader)

    def _createSpreadLightingShader(self):
        shader = BetterShader.loadCompute("Shader/GI/SpreadLighting.compute")
        self.spreadLightingNode = NodePath("SpreadLighting")
        self.spreadLightingNode.setShader(shader)

    def _createCopyShader(self):
        shader = BetterShader.loadCompute("Shader/GI/CopyResult.compute")
        self.copyResultNode = NodePath("CopyResult")
        self.copyResultNode.setShader(shader)

    def reloadShader(self):
        self._createCleanShader()
        self._createPopulateShader()
        self._createSpreadLightingShader()
        self._createCopyShader()

        if self.debugVoxels:
            self._setBoxShader()

        self.frameIndex = 0

    def _clearTexture(self, tex, clearVal=None):
        if clearVal is None:
            clearVal = Vec4(0)

        self.clearTextureNode.setShaderInput("target", tex)
        self.clearTextureNode.setShaderInput(
            "clearValue", clearVal)
        self._executeShader(
            self.clearTextureNode,
            self.cascadeSize * self.cascadeSize / 16,
            self.cascadeSize / 16)

    def process(self):

        self.frameIndex += 1

        # Process GI splitted over frames
        if self.frameIndex > self.iterations + 2:
            self.frameIndex = 1

        # TODO: Not all shader inputs need to be set everytime. Use PTAs
        # instead

        # print "Frame Index:", self.frameIndex

        if self.frameIndex == 1:
            # First pass: Read the reflective shadow maps, and populate the
            # 3D Grid with intial values

            atlas = self.pipeline.getLightManager().shadowComputeTarget
            atlasDepth = atlas.getDepthTexture()
            atlasColor = atlas.getColorTexture()
            atlasNormal = atlas.getAuxTexture(0)
            atlasSize = atlasDepth.getXSize()

            allLights = self.pipeline.getLightManager().getAllLights()
            casters = []

            # Collect the shadow caster sources from all lights
            for light in allLights:
                if light.hasShadows():
                    for source in light.getShadowSources():
                        casters.append((source, light))

            # Each shadow caster source contributes to the GI
            for index, packed in enumerate(casters):
                caster, light = packed
                factor = 0.0

                if light._getLightType() == LightType.Directional:
                    factor = 1.0

                relativeSize = float(caster.getResolution()) / atlasSize
                relativePos = caster.getAtlasPos()
                direction = light.direction
                color = light.color
                self.sourcesData[index] = UnalignedLMatrix4f(
                    relativePos.x, relativePos.y, relativeSize, factor,
                    caster.nearPlane, caster.farPlane, 0, 0,
                    direction.x, direction.y, direction.z, 0,
                    color.x, color.y, color.z, 0)
                self.mvpData[index] = UnalignedLMatrix4f(caster.mvp)

            # Clear VPL storages first
            texturesToClear = [
                (self.vplStorage, Vec4(0, 0, 0, 0)),
                (self.vplStorageTemp, Vec4(0, 0, 0, 0)),
                (self.colorStorage, Vec4(0, 0, 0, 0)),
                (self.colorStorageTemp, Vec4(0, 0, 0, 0))
            ]
            for tex, clearVal in texturesToClear:
                self._clearTexture(tex, clearVal)

            # Now populate with VPLs
            self.populateVPLNode.setShaderInput("atlasDepth", atlasDepth)
            self.populateVPLNode.setShaderInput("atlasColor", atlasColor)
            self.populateVPLNode.setShaderInput("atlasNormal", atlasNormal)
            self.populateVPLNode.setShaderInput("gridStart", self.gridStart)
            self.populateVPLNode.setShaderInput("gridEnd", self.gridEnd)
            self.populateVPLNode.setShaderInput(
                "gridSize", LVecBase3i(self.cascadeSize))
            self.populateVPLNode.setShaderInput("voxelSize", self.voxelSize)
            self.populateVPLNode.setShaderInput("lightCount", len(casters))
            self.populateVPLNode.setShaderInput("lightMVPData", self.mvpData)
            self.populateVPLNode.setShaderInput("lightData", self.sourcesData)
            self.populateVPLNode.setShaderInput("target", self.vplStorage)
            self.populateVPLNode.setShaderInput(
                "targetColor", self.colorStorage)
            self._executeShader(
                self.populateVPLNode, self.cascadeSize / 4,
                self.cascadeSize / 4, self.cascadeSize / 4)

        elif self.frameIndex < self.iterations + 2:
            # In the other frames, we spread the lighting. This can be
            # basically seen as a normal aware 3d blur
            self.spreadLightingNode.setShaderInput(
                "gridSize", LVecBase3i(self.cascadeSize))

            if self.frameIndex % 2 == 0:
                self.spreadLightingNode.setShaderInput(
                    "source", self.vplStorage)
                self.spreadLightingNode.setShaderInput(
                    "sourceColor", self.colorStorage)
                self.spreadLightingNode.setShaderInput(
                    "target", self.vplStorageTemp)
                self.spreadLightingNode.setShaderInput(
                    "targetColor", self.colorStorageTemp)

                self._executeShader(
                    self.spreadLightingNode, self.cascadeSize / 4,
                    self.cascadeSize / 4, self.cascadeSize / 4)

            else:
                self.spreadLightingNode.setShaderInput(
                    "source", self.vplStorageTemp)
                self.spreadLightingNode.setShaderInput(
                    "sourceColor", self.colorStorageTemp)
                self.spreadLightingNode.setShaderInput(
                    "target", self.vplStorage)
                self.spreadLightingNode.setShaderInput(
                    "targetColor", self.colorStorage)
                self._executeShader(
                    self.spreadLightingNode, self.cascadeSize / 4,
                    self.cascadeSize / 4, self.cascadeSize / 4)
        else:
            # Copy result in the last frame
            # print "Copied result"
            self.copyResultNode.setShaderInput("src", self.colorStorage)
            self.copyResultNode.setShaderInput("dest", self.resultStorage)
            self._executeShader(
                self.copyResultNode,
                self.cascadeSize * self.cascadeSize / 16,
                self.cascadeSize / 16)

    def bindTo(self, node):
        node.setShaderInput("GI_gridStart", self.gridStart)
        node.setShaderInput("GI_gridEnd", self.gridEnd)
        node.setShaderInput("GI_grid", self.vplStorage)
        node.setShaderInput("GI_gridColor", self.resultStorage)
        node.setShaderInput("GI_cascadeSize", self.cascadeSize)

    def _executeShader(self, node, threadsX, threadsY, threadsZ=1):
        # Retrieve the underlying ShaderAttrib
        sattr = node.get_attrib(ShaderAttrib)

        # Dispatch the compute shader, right now!
        Globals.base.graphicsEngine.dispatch_compute(
            (threadsX, threadsY, threadsZ), sattr, Globals.base.win.get_gsg())
