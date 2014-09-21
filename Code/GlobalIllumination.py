
from panda3d.core import Texture, NodePath, ShaderAttrib, Vec4, Vec3
from panda3d.core import Vec2, LMatrix4f, LVecBase3i
from panda3d.core import Mat4, OmniBoundingVolume
from panda3d.core import PStatCollector
from direct.stdpy.file import isfile, open, join

from Globals import Globals
from DebugObject import DebugObject
from BetterShader import BetterShader
from LightType import LightType
from GUI.BufferViewerGUI import BufferViewerGUI

from SettingsManager import SettingsManager

pstats_PopulateVoxelGrid = PStatCollector(
    "App:GlobalIllumnination:PopulateVoxelGrid")
pstats_GenerateVoxelOctree = PStatCollector(
    "App:GlobalIllumnination:GenerateVoxelOctree")
pstats_ClearGI = PStatCollector("App:GlobalIllumnination:Clear")
pstats_GenerateMipmaps = PStatCollector("App:GlobalIllumnination::GenerateMipmaps")

class VoxelSettingsManager(SettingsManager):

    def __init__(self):
        SettingsManager.__init__(self, "VoxelSettings")

    def _addDefaultSettings(self):

        self._addSetting("GridResolution", int, 256)
        self._addSetting("GridStart", Vec3, Vec3(0))
        self._addSetting("GridEnd", Vec3, Vec3(0))
        self._addSetting("StackSizeX", int, 32)
        self._addSetting("StackSizeY", int, 8)


class GlobalIllumination(DebugObject):

    """ This class handles the global illumination processing. It is still
    experimental, and thus not commented. """

    sceneRoot = "Demoscene.ignore/voxelized"
    updateEnabled = True

    def __init__(self, pipeline):
        DebugObject.__init__(self, "GlobalIllumnination")
        self.pipeline = pipeline

    @classmethod
    def setSceneRoot(self, sceneSrc):
        self.sceneRoot = sceneSrc

    @classmethod
    def setUpdateEnabled(self, enabled):
        self.updateEnabled = enabled

    def setup(self):
        """ Setups everything for the GI to work """
        self.debug("Setup ..")

        if self.pipeline.settings.useHardwarePCF:
            self.error(
                "Global Illumination does not work in combination with PCF!")
            import sys
            sys.exit(0)
            return

        self.settings = VoxelSettingsManager()
        self.settings.loadFromFile(join(self.sceneRoot, "voxels.ini"))

        self.debug(
            "Loaded voxels, grid resolution is", self.settings.GridResolution)

        self.gridScale = self.settings.GridEnd - self.settings.GridStart
        self.voxelSize = self.gridScale / float(self.settings.GridResolution)
        self.entrySize = Vec2(
            1.0 / float(self.settings.StackSizeX), 1.0 / float(self.settings.StackSizeY))
        self.frameIndex = 0

        invVoxelSize = Vec3(
            1.0 / self.voxelSize.x, 1.0 / self.voxelSize.y, 1.0 / self.voxelSize.z)
        invVoxelSize.normalize()
        self.normalizationFactor = invVoxelSize / \
            float(self.settings.GridResolution)

        # Debugging of voxels, VERY slow
        self.debugVoxels = False

        if self.debugVoxels:
            self.createVoxelDebugBox()

        # Load packed voxels
        packedVoxels = Globals.loader.loadTexture(
            join(self.sceneRoot, "voxels.png"))
        packedVoxels.setFormat(Texture.FRgba8)
        packedVoxels.setComponentType(Texture.TUnsignedByte)
        # packedVoxels.setKeepRamImage(False)

        # Create 3D Texture to store unpacked voxels
        self.unpackedVoxels = Texture("Unpacked voxels")
        self.unpackedVoxels.setup3dTexture(self.settings.GridResolution, self.settings.GridResolution, self.settings.GridResolution,
                                           Texture.TFloat, Texture.FRgba8)
        self.unpackedVoxels.setMinfilter(Texture.FTLinearMipmapLinear)
        self.unpackedVoxels.setMagfilter(Texture.FTLinear)

        self.unpackVoxels = NodePath("unpackVoxels")
        self.unpackVoxels.setShader(
            BetterShader.loadCompute("Shader/GI/UnpackVoxels.compute"))

        print "setting inputs .."
        self.unpackVoxels.setShaderInput("packedVoxels", packedVoxels)
        print "setting inputs .."
        self.unpackVoxels.setShaderInput(
            "stackSizeX", LVecBase3i(self.settings.StackSizeX))
        print "setting inputs .."
        self.unpackVoxels.setShaderInput(
            "gridSize", LVecBase3i(self.settings.GridResolution))
        print "setting inputs .."
        self.unpackVoxels.setShaderInput("destination", self.unpackedVoxels)
        print "executing shader .."
        self._executeShader(
            self.unpackVoxels, self.settings.GridResolution / 8, self.settings.GridResolution / 8, self.settings.GridResolution / 8)

        print "creating direct radiance texture .."
        # Create 3D Texture to store direct radiance
        self.directRadianceCache = Texture("Direct radiance cache")
        self.directRadianceCache.setup3dTexture(self.settings.GridResolution, self.settings.GridResolution, self.settings.GridResolution,
                                           Texture.TInt, Texture.FR32i)

        self.directRadiance = Texture("Direct radiance")
        self.directRadiance.setup3dTexture(self.settings.GridResolution, self.settings.GridResolution, self.settings.GridResolution,
                                           Texture.TFloat, Texture.FRgba16)

        print "setting texture states .."
        for prepare in [self.directRadiance, self.unpackedVoxels]:
            prepare.setMagfilter(Texture.FTLinear)
            prepare.setMinfilter(Texture.FTLinearMipmapLinear)
            prepare.setWrapU(Texture.WMBorderColor)
            prepare.setWrapV(Texture.WMBorderColor)
            prepare.setWrapW(Texture.WMBorderColor)
            prepare.setBorderColor(Vec4(0,0,0,1))

        self.unpackedVoxels.setBorderColor(Vec4(0))
        # self.directRadiance.setBorderColor(Vec4(0))

        self.populateVPLNode = NodePath("PopulateVPLs")
        self.clearTextureNode = NodePath("ClearTexture")
        self.copyTextureNode = NodePath("CopyTexture")
        self.generateMipmapsNode = NodePath("GenerateMipmaps")
        self.convertGridNode = NodePath("ConvertGrid")


        if False:
            surroundingBox = Globals.loader.loadModel(
                "Models/CubeFix/Model.egg")
            surroundingBox.setPos(self.settings.GridStart)
            surroundingBox.setScale(self.gridScale)

            # surroundingBox.setTwoSided(True)
            surroundingBox.flattenStrong()
            surroundingBox.reparentTo(Globals.render)

        self.bindTo(self.populateVPLNode, "giData")
        self.reloadShader()

        self._generateMipmaps(self.unpackedVoxels)

    def _generateMipmaps(self, tex):
        """ Generates all mipmaps for a 3D texture, using a gaussian function """

        pstats_GenerateMipmaps.start()
        currentMipmap = 0
        computeSize = self.settings.GridResolution
        self.generateMipmapsNode.setShaderInput("source", tex)
        self.generateMipmapsNode.setShaderInput(
            "pixelSize", 1.0 / self.settings.GridResolution)

        while computeSize >= 2:
            computeSize /= 2
            self.generateMipmapsNode.setShaderInput(
                "sourceMipmap", LVecBase3i(currentMipmap))
            self.generateMipmapsNode.setShaderInput(
                "currentMipmapSize", LVecBase3i(computeSize))
            self.generateMipmapsNode.setShaderInput(
                "dest", tex, False, True, -1, currentMipmap + 1)
            self._executeShader(self.generateMipmapsNode,
                                (computeSize + 7) / 8,
                                (computeSize + 7) / 8,
                                (computeSize + 7) / 8)
            currentMipmap += 1

        pstats_GenerateMipmaps.stop()

    def createVoxelDebugBox(self):
        box = Globals.loader.loadModel("box")

        gridVisualizationSize = 64
        box.setScale(self.voxelSize)
        box.setPos(self.settings.GridStart)
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

    def _createConvertShader(self):
        shader = BetterShader.loadCompute("Shader/GI/ConvertGrid.compute")
        self.convertGridNode.setShader(shader)

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
        self._createConvertShader()

        if self.debugVoxels:
            self._setBoxShader()
        self.frameIndex = 0

    def _clear3DTexture(self, tex, clearVal=None):
        """ Clears a 3D Texture to <clearVal> """
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
        """ Copies texture <src> into texture <dest>. The same size is assumed """
        self.copyTextureNode.setShaderInput("src", src)
        self.copyTextureNode.setShaderInput("dest", dest)
        self._executeShader(
            self.copyTextureNode,
            (src.getXSize() + 15) / 16,
            (src.getYSize() + 15) / 16)

    def process(self):

        self.frameIndex += 1

        # Process GI splitted over frames
        if self.frameIndex > 2:
            self.frameIndex = 1

        if not self.updateEnabled:
            return

        # TODO: Not all shader inputs need to be set everytime. Use PTAs instead, over even better,
        # cache the shader inputs in a ShaderAttrib

        if self.frameIndex == 1:

            # First pass: Read the reflective shadow maps, and populate the
            # 3D Grid with intial values

            # Clear radiance texture
            pstats_ClearGI.start()
            self._clear3DTexture(self.directRadianceCache, Vec4(0))
            pstats_ClearGI.stop()

            pstats_PopulateVoxelGrid.start()
            
            # Get texture handles
            atlas = self.pipeline.getLightManager().shadowComputeTarget
            atlasDepth = atlas.getDepthTexture()
            atlasColor = atlas.getColorTexture()
            atlasSize = atlasDepth.getXSize()

            # Fetch the sun light and it's shadow sources from the light manager

            allLights = self.pipeline.getLightManager().getAllLights()
            casterLight = None
            casterSource = None

            # Collect the shadow caster sources from the sun light
            # (A directional light may have multiple sources, e.g. for PSSM)
            # TODO: Currently we only use the first shadow source. Make it use all sources
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

            # Now populate the Voxel Grid, based on the RSM (Reflective Shadow Map)
            self.populateVPLNode.setShaderInput("atlasDepth", atlasDepth)
            self.populateVPLNode.setShaderInput("atlasColor", atlasColor)
            self.populateVPLNode.setShaderInput("lightMVP", mvpData)
            self.populateVPLNode.setShaderInput("lightData", sourceData)
            self.populateVPLNode.setShaderInput(
                "lightLens", casterSource.cameraNode)
            self.populateVPLNode.setShaderInput(
                "mainRender", Globals.base.render)
            self.populateVPLNode.setShaderInput(
                "target", self.directRadianceCache, True, True, -1, 0)

            # Execute the shader
            self._executeShader(
                self.populateVPLNode, resolution / 16, resolution / 16)

            pstats_PopulateVoxelGrid.stop()
            
        elif self.frameIndex == 2:

            # In this frame we generate the mipmaps for the voxel grid

            # Copy the cache to the actual texture
            self.convertGridNode.setShaderInput("src", self.directRadianceCache)
            self.convertGridNode.setShaderInput("dest", self.directRadiance)
            self._executeShader(
                self.convertGridNode, self.settings.GridResolution / 8, self.settings.GridResolution / 8, self.settings.GridResolution / 8)

            # Generate the mipmaps for the voxel grid
            pstats_GenerateVoxelOctree.start()
            self._generateMipmaps(self.directRadiance)
            pstats_GenerateVoxelOctree.stop()


    def bindTo(self, node, prefix):
        """ Binds all required shader inputs to a target to compute / display
        the global illumination """
        node.setShaderInput(prefix + ".gridStart", self.settings.GridStart)
        node.setShaderInput(prefix + ".gridEnd", self.settings.GridEnd)
        node.setShaderInput(
            prefix + ".stackSizeX", LVecBase3i(self.settings.StackSizeX))
        node.setShaderInput(
            prefix + ".stackSizeY", LVecBase3i(self.settings.StackSizeY))
        node.setShaderInput(
            prefix + ".gridSize",  LVecBase3i(self.settings.GridResolution))
        node.setShaderInput(prefix + ".voxelSize", self.voxelSize)
        node.setShaderInput(prefix + ".gridScale", self.gridScale)
        node.setShaderInput(prefix + ".entrySize", self.entrySize)
        node.setShaderInput(
            prefix + ".normalizationFactor", self.normalizationFactor)
        node.setShaderInput(prefix + ".voxels", self.directRadiance)
        node.setShaderInput(prefix + ".geometry", self.unpackedVoxels)

    def _executeShader(self, node, threadsX, threadsY, threadsZ=1):
        """ Executes a compute shader, fetching the shader attribute from a NodePath """
        sattr = node.get_attrib(ShaderAttrib)
        Globals.base.graphicsEngine.dispatch_compute(
            (threadsX, threadsY, threadsZ), sattr, Globals.base.win.get_gsg())
