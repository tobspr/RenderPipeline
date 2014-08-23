
from panda3d.core import Texture, NodePath, ShaderAttrib, Vec4, Vec3
from panda3d.core import Vec2, LMatrix4f, LVecBase3i
from panda3d.core import Mat4, OmniBoundingVolume

from Globals import Globals
from DebugObject import DebugObject
from BetterShader import BetterShader
from LightType import LightType
from GUI.BufferViewerGUI import BufferViewerGUI


from panda3d.core import PStatCollector

pstats_PopulateVoxelGrid = PStatCollector("App:GlobalIllumnination:PopulateVoxelGrid")
pstats_GenerateVoxelOctree = PStatCollector("App:GlobalIllumnination:GenerateVoxelOctree")
pstats_ClearGI = PStatCollector("App:GlobalIllumnination:Clear")


class GlobalIllumnination(DebugObject):

    """ This class handles the global illumination processing """

    def __init__(self, pipeline):
        DebugObject.__init__(self, "GlobalIllumnination")
        self.pipeline = pipeline

    def _allocTexture(self):
        tex = Texture("tex")
        tex.setup2dTexture(
            self.gridSize * self.stackSizeX, self.gridSize * self.stackSizeY,
            Texture.TFloat, Texture.FRgba8)
        return tex

    def setup(self):
        """ Setups everything for the GI to work """
        self.debug("Setup ..")

        # Constants, will later be loaded from disk
        self.gridSize = 256
        self.stackSizeX = 32
        self.stackSizeY = 8
        self.gridStart = Vec3(-97.0472946167, -56.2713127136, -2.40248203278)
        self.gridEnd = Vec3(90.9954071045, 60.1403465271, 72.4716720581)

        # self.gridStart = Vec3(-6.0, -6.0, -0.996201992035)
        # self.gridEnd = Vec3(6.0, 6.0, 7.78633880615)


        self.gridScale = self.gridEnd - self.gridStart
        self.voxelSize = self.gridScale / float(self.gridSize)
        self.entrySize = Vec2(
            1.0 / float(self.stackSizeX), 1.0 / float(self.stackSizeY))
        self.frameIndex = 0

        invVoxelSize = Vec3(1.0 / self.voxelSize.x, 1.0 / self.voxelSize.y, 1.0 / self.voxelSize.z)
        invVoxelSize.normalize()
        self.normalizationFactor = invVoxelSize / float(self.gridSize)

        # Debugging of voxels, VERY slow
        self.debugVoxels = False

        if self.debugVoxels:
            self.createVoxelDebugBox()

        # Load packed voxels
        packedVoxels = Globals.loader.loadTexture(
            "Demoscene.ignore/voxelized/voxels.png")
        packedVoxels.setFormat(Texture.FRgba8)
        packedVoxels.setComponentType(Texture.TUnsignedByte)
        # packedVoxels.setKeepRamImage(False)

        # Create 3D Texture to store unpacked voxels
        self.unpackedVoxels = Texture("Unpacked voxels")
        self.unpackedVoxels.setup3dTexture(self.gridSize, self.gridSize, self.gridSize,
                                           Texture.TFloat, Texture.FRgba8)
        self.unpackedVoxels.setMinfilter(Texture.FTLinearMipmapLinear)
        self.unpackedVoxels.setMagfilter(Texture.FTLinear)

        self.unpackVoxels = NodePath("unpackVoxels")
        self.unpackVoxels.setShader(
            BetterShader.loadCompute("Shader/GI/UnpackVoxels.compute"))
        self.unpackVoxels.setShaderInput("packedVoxels", packedVoxels)
        self.unpackVoxels.setShaderInput("stackSizeX", LVecBase3i(self.stackSizeX))
        self.unpackVoxels.setShaderInput("gridSize", LVecBase3i(self.gridSize))
        self.unpackVoxels.setShaderInput("destination", self.unpackedVoxels)
        self._executeShader(
            self.unpackVoxels, self.gridSize / 8, self.gridSize / 8, self.gridSize / 8)



        # Create 3D Texture to store direct radiance
        self.directRadiance = Texture("Direct radiance")
        self.directRadiance.setup3dTexture(self.gridSize, self.gridSize, self.gridSize,
                                           Texture.TFloat, Texture.FRgba8)

        for prepare in [self.directRadiance, self.unpackedVoxels]:
            prepare.setMagfilter(Texture.FTLinear)
            prepare.setMinfilter(Texture.FTLinearMipmapLinear)
            prepare.setWrapU(Texture.WMBorderColor)
            prepare.setWrapV(Texture.WMBorderColor)
            prepare.setWrapW(Texture.WMBorderColor)
            prepare.setBorderColor(Vec4(0))


        self.populateVPLNode = NodePath("PopulateVPLs")
        self.clearTextureNode = NodePath("ClearTexture")
        self.copyTextureNode = NodePath("CopyTexture")
        self.generateMipmapsNode = NodePath("GenerateMipmaps")

        surroundingBox = loader.loadModel(
            "Demoscene.ignore/CubeOpen/Model.egg")
        surroundingBox.setPos(self.gridStart)
        surroundingBox.setScale(self.gridScale)
        surroundingBox.reparentTo(render)

        self.bindTo(self.populateVPLNode, "giData")
        self.reloadShader()

        self._generateMipmaps(self.unpackedVoxels)

    def _generateMipmaps(self, tex):
        # Generate geometry mipmaps
        currentMipmap = 0
        computeSize = self.gridSize
        self.generateMipmapsNode.setShaderInput("source", tex)
        self.generateMipmapsNode.setShaderInput("pixelSize", 1.0 / self.gridSize)

        while computeSize >= 2:
            computeSize /= 2
            self.generateMipmapsNode.setShaderInput("sourceMipmap", LVecBase3i(currentMipmap))
            self.generateMipmapsNode.setShaderInput("currentMipmapSize", LVecBase3i(computeSize))
            self.generateMipmapsNode.setShaderInput(
                "dest", tex, False, True, -1, currentMipmap + 1)
            self._executeShader(self.generateMipmapsNode,
                                (computeSize+7) / 8, 
                                (computeSize+7) / 8, 
                                (computeSize+7) / 8)
            currentMipmap += 1

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
        box.setShaderInput("giGrid", self.geometryTexture)
        box.setShaderInput("realGridSize", self.cascadeSize)
        box.setShaderInput("giColorGrid", self.vplTextureResult)
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
        self.clearTextureNode.setShader(shader)

    def _createCopyShader(self):
        shader = BetterShader.loadCompute("Shader/GI/CopyResult.compute")
        self.copyTextureNode.setShader(shader)

    def _createPopulateShader(self):
        shader = BetterShader.loadCompute("Shader/GI/PopulateVPL.compute")
        self.populateVPLNode.setShader(shader)

    def _createGenerateMipmapsShader(self):
        shader = BetterShader.loadCompute("Shader/GI/GenerateMipmaps.compute")
        self.generateMipmapsNode.setShader(shader)

    def reloadShader(self):
        self._createCleanShader()
        self._createPopulateShader()
        self._createGenerateMipmapsShader()

        if self.debugVoxels:
            self._setBoxShader()
        self.frameIndex = 0

    def _clear3DTexture(self, tex, clearVal=None):
        if clearVal is None:
            clearVal = Vec4(0)

        self.clearTextureNode.setShaderInput("target", tex, False, True, -1, 0)
        self.clearTextureNode.setShaderInput(
            "clearValue", clearVal)

        self._executeShader(
            self.clearTextureNode,
            (tex.getXSize() + 7) / 8,
            (tex.getYSize() + 7) / 8,
            (tex.getZSize() + 7) / 8)

    def _copyTexture(self, src, dest):
        self.copyTextureNode.setShaderInput("src", src)
        self.copyTextureNode.setShaderInput("dest", dest)
        self._executeShader(
            self.copyTextureNode,
            (src.getXSize() + 15) / 16,
            (src.getYSize() + 15) / 16)

    def process(self):

        self.frameIndex += 1

        # Process GI splitted over frames
        if self.frameIndex > 1:
            self.frameIndex = 1

        # TODO: Not all shader inputs need to be set everytime. Use PTAs
        # instead

        if self.frameIndex == 1:

            # First pass: Read the reflective shadow maps, and populate the
            # 3D Grid with intial values

            # Clear radiance
            pstats_ClearGI.start()
            self._clear3DTexture(self.directRadiance, Vec4(0))
            pstats_ClearGI.stop()


            pstats_PopulateVoxelGrid.start()
            atlas = self.pipeline.getLightManager().shadowComputeTarget
            atlasDepth = atlas.getDepthTexture()
            atlasColor = atlas.getColorTexture()
            atlasSize = atlasDepth.getXSize()

            # Todo: Do this for all lights
            allLights = self.pipeline.getLightManager().getAllLights()

            # Find the light where to cast gi from
            casterLight = None
            casterSource = None

            # Collect the shadow caster sources from the first directional
            # light
            for light in allLights:
                if light.hasShadows() and \
                   light._getLightType() == LightType.Directional:
                    casterLight = light
                    casterSource = casterLight.getShadowSources()[0]

            resolution = casterSource.getResolution()
            relativePos = casterSource.getAtlasPos() * atlasSize
            direction = light.direction
            color = light.color
            sourceData = LMatrix4f(
                relativePos.x, relativePos.y, resolution, 0.0,
                casterSource.nearPlane, casterSource.farPlane, 0, 0,
                direction.x, direction.y, direction.z, 0,
                color.x, color.y, color.z, 0)
            mvpData = LMatrix4f(casterSource.mvp)

            # Now populate with VPLs
            self.populateVPLNode.setShaderInput("atlasDepth", atlasDepth)
            self.populateVPLNode.setShaderInput("atlasColor", atlasColor)
            self.populateVPLNode.setShaderInput("lightMVP", mvpData)
            self.populateVPLNode.setShaderInput("lightData", sourceData)
            self.populateVPLNode.setShaderInput(
                "lightLens", casterSource.cameraNode)
            self.populateVPLNode.setShaderInput(
                "mainRender", Globals.base.render)
            self.populateVPLNode.setShaderInput(
                "target", self.directRadiance, True, True, -1, 0)

            self._executeShader(
                self.populateVPLNode, resolution / 16, resolution / 16)

            pstats_PopulateVoxelGrid.stop()

        # elif self.frameIndex == 2:

            pstats_GenerateVoxelOctree.start()
            # In this frame we generate the mipmaps for the voxel grid
            currentMipmap = 0
            computeSize = self.gridSize

            self._generateMipmaps(self.directRadiance)

            pstats_GenerateVoxelOctree.start()
        # In the other frames, we spread the lighting. This can be
        # basically seen as a normal aware 3d blur
        #     self.spreadLightingNode.setShaderInput(
        #         "gridSize", LVecBase3i(self.cascadeSize))
        #     self.spreadLightingNode.setShaderInput(
        #         "geometryTex", self.geometryTexture)
        #     if self.frameIndex % 2 == 0:
        #         self.spreadLightingNode.setShaderInput(
        #             "source", self.vplTexturePing)
        #         self.spreadLightingNode.setShaderInput(
        #             "target", self.vplTexturePong)
        #         self._executeShader(
        #             self.spreadLightingNode, self.cascadeSize / 4,
        #             self.cascadeSize / 4, self.cascadeSize / 4)
        #     else:
        #         self.spreadLightingNode.setShaderInput(
        #             "source", self.vplTexturePong)
        #         self.spreadLightingNode.setShaderInput(
        #             "target", self.vplTexturePing)
        #         self._executeShader(
        #             self.spreadLightingNode, self.cascadeSize / 4,
        #             self.cascadeSize / 4, self.cascadeSize / 4)
        # else:
        # Copy result in the last frame
        #     self.copyResultNode.setShaderInput("src", self.vplTexturePing)
        #     self.copyResultNode.setShaderInput("dest", self.vplTextureResult)
        #     self._executeShader(
        #         self.copyResultNode,
        #         self.cascadeSize * self.cascadeSize / 16,
        #         self.cascadeSize / 16)
    def bindTo(self, node, prefix):
        node.setShaderInput(prefix + ".gridStart", self.gridStart)
        node.setShaderInput(prefix + ".gridEnd", self.gridEnd)
        node.setShaderInput(
            prefix + ".stackSizeX", LVecBase3i(self.stackSizeX))
        node.setShaderInput(
            prefix + ".stackSizeY", LVecBase3i(self.stackSizeY))
        node.setShaderInput(prefix + ".gridSize",  LVecBase3i(self.gridSize))
        node.setShaderInput(prefix + ".voxelSize", self.voxelSize)
        node.setShaderInput(prefix + ".gridScale", self.gridScale)
        node.setShaderInput(prefix + ".entrySize", self.entrySize)
        node.setShaderInput(prefix + ".normalizationFactor", self.normalizationFactor)
        node.setShaderInput(prefix + ".voxels", self.directRadiance)
        node.setShaderInput(prefix + ".geometry", self.unpackedVoxels)

    def _executeShader(self, node, threadsX, threadsY, threadsZ=1):
        # Retrieve the underlying ShaderAttrib
        sattr = node.get_attrib(ShaderAttrib)

        # Dispatch the compute shader, right now!
        Globals.base.graphicsEngine.dispatch_compute(
            (threadsX, threadsY, threadsZ), sattr, Globals.base.win.get_gsg())
