
from panda3d.core import Texture, NodePath, ShaderAttrib, Vec4, Vec3
from panda3d.core import Vec2, LMatrix4f, LVecBase3i, Camera, Mat4
from panda3d.core import Mat4, OmniBoundingVolume, OrthographicLens
from panda3d.core import PStatCollector, BoundingBox, Point3, CullFaceAttrib
from panda3d.core import DepthTestAttrib, PTALVecBase3f
from direct.stdpy.file import isfile, open, join

from Globals import Globals
from DebugObject import DebugObject
from BetterShader import BetterShader
from LightType import LightType
from GUI.BufferViewerGUI import BufferViewerGUI
from RenderTarget import RenderTarget
from GIHelperLight import GIHelperLight
from LightType import LightType
from SettingsManager import SettingsManager

import time
import math

pstats_PopulateVoxelGrid = PStatCollector(
    "App:GlobalIllumnination:PopulateVoxelGrid")
pstats_GenerateVoxelOctree = PStatCollector(
    "App:GlobalIllumnination:GenerateVoxelOctree")
pstats_ClearGI = PStatCollector("App:GlobalIllumnination:Clear")
pstats_GenerateMipmaps = PStatCollector("App:GlobalIllumnination::GenerateMipmaps")

class GlobalIllumination(DebugObject):

    """ This class handles the global illumination processing. It is still
    experimental, and thus not commented. """

    updateEnabled = False

    def __init__(self, pipeline):
        DebugObject.__init__(self, "GlobalIllumnination")
        self.pipeline = pipeline

        self.targetCamera = Globals.base.cam
        self.targetSpace = Globals.base.render

        self.voxelBaseResolution = 512 * 4
        self.voxelGridSizeWS = Vec3(50, 50, 20)
        self.voxelGridResolution = LVecBase3i(512, 512, 128)
        self.targetLight = None
        self.helperLight = None
        self.ptaGridPos = PTALVecBase3f.emptyArray(1)
        self.gridPos = Vec3(0)

    @classmethod
    def setUpdateEnabled(self, enabled):
        self.updateEnabled = enabled

    def setTargetLight(self, light):
        """ Sets the sun light which is the main source of GI """

        if light._getLightType() != LightType.Directional:
            self.error("setTargetLight expects a directional light!")
            return

        self.targetLight = light
        self._createHelperLight()

    def _prepareVoxelScene(self):
        """ Creates the internal buffer to voxelize the scene on the fly """
        self.voxelizeScene = Globals.render
        self.voxelizeCamera = Camera("VoxelizeScene")
        self.voxelizeCameraNode = self.voxelizeScene.attachNewNode(self.voxelizeCamera)
        self.voxelizeLens = OrthographicLens()
        self.voxelizeLens.setFilmSize(self.voxelGridSizeWS.x*2, self.voxelGridSizeWS.y*2)
        self.voxelizeLens.setNearFar(0.0, self.voxelGridSizeWS.x*2)
        self.voxelizeCamera.setLens(self.voxelizeLens)
        self.voxelizeCamera.setTagStateKey("VoxelizePassShader")

        self.targetSpace.setTag("VoxelizePassShader", "Default")

        self.voxelizeCameraNode.setPos(0,0,0)
        self.voxelizeCameraNode.lookAt(0,0,0)

        self.voxelizeTarget = RenderTarget("DynamicVoxelization")
        self.voxelizeTarget.setSize(self.voxelBaseResolution) 
        # self.voxelizeTarget.addDepthTexture()
        # self.voxelizeTarget.addColorTexture()
        # self.voxelizeTarget.setColorBits(16)
        self.voxelizeTarget.setSource(self.voxelizeCameraNode, Globals.base.win)
        self.voxelizeTarget.prepareSceneRender()

        self.voxelizeTarget.getQuad().node().removeAllChildren()
        self.voxelizeTarget.getInternalRegion().setSort(-400)
        self.voxelizeTarget.getInternalBuffer().setSort(-399)

        # for tex in [self.voxelizeTarget.getColorTexture()]:
        #     tex.setWrapU(Texture.WMClamp)
        #     tex.setWrapV(Texture.WMClamp)
        #     tex.setMinfilter(Texture.FTNearest)
        #     tex.setMagfilter(Texture.FTNearest)

        voxelSize = Vec3(
                self.voxelGridSizeWS.x * 2.0 / self.voxelGridResolution.x,
                self.voxelGridSizeWS.y * 2.0 / self.voxelGridResolution.y,
                self.voxelGridSizeWS.z * 2.0 / self.voxelGridResolution.z
            )

        self.targetSpace.setShaderInput("dv_gridSize", self.voxelGridSizeWS * 2)
        self.targetSpace.setShaderInput("dv_voxelSize", voxelSize)
        self.targetSpace.setShaderInput("dv_gridResolution", self.voxelGridResolution)


    def _createVoxelizeState(self):
        """ Creates the tag state and loades the voxelizer shader """
        self.voxelizeShader = BetterShader.load(
            "Shader/GI/Voxelize.vertex",
            "Shader/GI/Voxelize.fragment"
            # "Shader/GI/Voxelize.geometry"
            )

        initialState = NodePath("VoxelizerState")
        initialState.setShader(self.voxelizeShader, 50)
        initialState.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullNone))
        initialState.setDepthWrite(False)
        initialState.setDepthTest(False)
        initialState.setAttrib(DepthTestAttrib.make(DepthTestAttrib.MNone))

        initialState.setShaderInput("dv_dest_tex", self.voxelGenTex)

        self.voxelizeCamera.setTagState(
            "Default", initialState.getState())

    def _createHelperLight(self):
        """ Creates the helper light. We can't use the main directional light
        because it uses PSSM, so we need an extra shadow map """
        self.helperLight = GIHelperLight()
        self.helperLight.setPos(Vec3(50,50,100))
        self.helperLight.setShadowMapResolution(512)
        self.helperLight.setFilmSize(math.sqrt( (self.voxelGridSizeWS.x**2) * 2) * 2 )
        self.helperLight.setCastsShadows(True)
        self.pipeline.addLight(self.helperLight)

        self.targetSpace.setShaderInput("dv_uv_size", 
            float(self.helperLight.shadowResolution) / self.pipeline.settings.shadowAtlasSize)
        self.targetSpace.setShaderInput("dv_atlas", 
            self.pipeline.getLightManager().getAtlasTex())

        self._updateGridPos()

    def setup(self):
        """ Setups everything for the GI to work """

        # if self.pipeline.settings.useHardwarePCF:
        #     self.fatal(
        #         "Global Illumination does not work in combination with PCF!")
        #     return

        self._prepareVoxelScene()

        # Create 3D Texture to store the voxel generation grid
        self.voxelGenTex = Texture("VoxelsTemp")
        self.voxelGenTex.setup3dTexture(self.voxelGridResolution.x, self.voxelGridResolution.y, self.voxelGridResolution.z,
                                           Texture.TInt, Texture.FR32i)
        self.voxelGenTex.setMinfilter(Texture.FTLinearMipmapLinear)
        self.voxelGenTex.setMagfilter(Texture.FTLinear)

        # Create 3D Texture which is a copy of the voxel generation grid but
        # stable, as the generation grid is updated part by part
        self.voxelStableTex = Texture("VoxelsStable")
        self.voxelStableTex.setup3dTexture(self.voxelGridResolution.x, self.voxelGridResolution.y, self.voxelGridResolution.z,
                                           Texture.TFloat, Texture.FRgba8)
        self.voxelStableTex.setMinfilter(Texture.FTLinearMipmapLinear)
        self.voxelStableTex.setMagfilter(Texture.FTLinear)        

        for prepare in [self.voxelGenTex, self.voxelStableTex]:
            prepare.setMagfilter(Texture.FTLinear)
            prepare.setMinfilter(Texture.FTLinearMipmapLinear)
            prepare.setWrapU(Texture.WMBorderColor)
            prepare.setWrapV(Texture.WMBorderColor)
            prepare.setWrapW(Texture.WMBorderColor)
            prepare.setBorderColor(Vec4(0,0,0,0))

        self.voxelGenTex.setMinfilter(Texture.FTNearest)
        self.voxelGenTex.setMagfilter(Texture.FTNearest)
        self.voxelGenTex.setWrapU(Texture.WMClamp)
        self.voxelGenTex.setWrapV(Texture.WMClamp)
        self.voxelGenTex.setWrapW(Texture.WMClamp)

        # self.voxelStableTex.generateRamMipmapImages()   

        self._createVoxelizeState()

        self.clearTextureNode = NodePath("ClearTexture")
        self.copyTextureNode = NodePath("CopyTexture")
        self.generateMipmapsNode = NodePath("GenerateMipmaps")
        self.convertGridNode = NodePath("ConvertGrid")

        self.reloadShader()

    def _generateMipmaps(self, tex):
        """ Generates all mipmaps for a 3D texture, using a gaussian function """

        pstats_GenerateMipmaps.start()
        currentMipmap = 0
        computeSize = LVecBase3i(self.voxelGridResolution)
        self.generateMipmapsNode.setShaderInput("source", tex)
        self.generateMipmapsNode.setShaderInput(
            "pixelSize", 1.0 / computeSize.x)

        while computeSize.z > 1:
            computeSize /= 2
            self.generateMipmapsNode.setShaderInput(
                "sourceMipmap", LVecBase3i(currentMipmap))
            self.generateMipmapsNode.setShaderInput(
                "currentMipmapSize", LVecBase3i(computeSize))
            self.generateMipmapsNode.setShaderInput(
                "dest", tex, False, True, -1, currentMipmap + 1)
            self._executeShader(self.generateMipmapsNode,
                                (computeSize.x + 7) / 8,
                                (computeSize.y + 7) / 8,
                                (computeSize.z + 7) / 8)
            currentMipmap += 1

        pstats_GenerateMipmaps.stop()

    def _createCleanShader(self):
        shader = BetterShader.loadCompute("Shader/GI/ClearTexture.compute")
        self.clearTextureNode.setShader(shader)

    def _createConvertShader(self):
        shader = BetterShader.loadCompute("Shader/GI/ConvertGrid.compute")
        self.convertGridNode.setShader(shader)

    def _createGenerateMipmapsShader(self):
        shader = BetterShader.loadCompute("Shader/GI/GenerateMipmaps.compute")
        self.generateMipmapsNode.setShader(shader)

    def reloadShader(self):
        self._createCleanShader()
        self._createGenerateMipmapsShader()
        self._createConvertShader()
        self._createVoxelizeState()
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

    def _updateGridPos(self):

        snap = 32.0
        stepSizeX = float(self.voxelGridSizeWS.x * 2.0) / float(self.voxelGridResolution.x) * snap
        stepSizeY = float(self.voxelGridSizeWS.y * 2.0) / float(self.voxelGridResolution.y) * snap
        stepSizeZ = float(self.voxelGridSizeWS.z * 2.0) / float(self.voxelGridResolution.z) * snap

        self.gridPos = self.targetCamera.getPos(self.targetSpace)
        self.gridPos.x -= self.gridPos.x % stepSizeX
        self.gridPos.y -= self.gridPos.y % stepSizeY
        self.gridPos.z -= self.gridPos.z % stepSizeZ

    def process(self):
        if self.targetLight is None:
            self.fatal("The GI cannot work without a target light! Set one "
                "with setTargetLight() first!")

        if not self.updateEnabled:
            self.voxelizeTarget.setActive(False)
            return

        direction = self.targetLight.getDirection()

        # time.sleep(0.4)

        if self.frameIndex == 0:
            # Find out cam pos
            
            self.targetSpace.setShaderInput("dv_uv_start", 
                self.helperLight.shadowSources[0].getAtlasPos())

            self.voxelizeTarget.setActive(True)
            # self.voxelizeTarget.setActive(False)

            self.voxelizeLens.setFilmSize(self.voxelGridSizeWS.y*2, self.voxelGridSizeWS.z*2)
            self.voxelizeLens.setNearFar(0.0, self.voxelGridSizeWS.x*2)

            self.targetSpace.setShaderInput("dv_mvp", Mat4(self.helperLight.shadowSources[0].mvp))
            self.targetSpace.setShaderInput("dv_gridStart", self.gridPos - self.voxelGridSizeWS)
            self.targetSpace.setShaderInput("dv_gridEnd", self.gridPos + self.voxelGridSizeWS)
            self.targetSpace.setShaderInput("dv_lightdir", direction)

            # Clear textures
            self._clear3DTexture(self.voxelGenTex, Vec4(0,0,0,0))

            # Voxelize from x axis
            self.voxelizeCameraNode.setPos(self.gridPos - Vec3(self.voxelGridSizeWS.x, 0, 0))
            self.voxelizeCameraNode.lookAt(self.gridPos)
            self.targetSpace.setShaderInput("dv_direction", LVecBase3i(0))


        elif self.frameIndex == 1:
            # Voxelize from y axis

            # self.voxelizeTarget.setActive(False)

            self.voxelizeLens.setFilmSize(self.voxelGridSizeWS.x*2, self.voxelGridSizeWS.z*2)
            self.voxelizeLens.setNearFar(0.0, self.voxelGridSizeWS.y*2)

            self.voxelizeCameraNode.setPos(self.gridPos - Vec3(0, self.voxelGridSizeWS.y, 0))
            self.voxelizeCameraNode.lookAt(self.gridPos)
            self.targetSpace.setShaderInput("dv_direction", LVecBase3i(1))

        elif self.frameIndex == 2:

            # self.voxelizeTarget.setActive(False)
            # Voxelize from z axis
            self.voxelizeLens.setFilmSize(self.voxelGridSizeWS.x*2, self.voxelGridSizeWS.y*2)
            self.voxelizeLens.setNearFar(0.0, self.voxelGridSizeWS.z*2)

            self.voxelizeCameraNode.setPos(self.gridPos + Vec3(0, 0, self.voxelGridSizeWS.z))
            self.voxelizeCameraNode.lookAt(self.gridPos)
            self.targetSpace.setShaderInput("dv_direction", LVecBase3i(2))

        elif self.frameIndex == 3:


            self.voxelizeTarget.setActive(False)

            # Copy the cache to the actual texture
            self.convertGridNode.setShaderInput("src", self.voxelGenTex)
            self.convertGridNode.setShaderInput("dest", self.voxelStableTex)
            self._executeShader(
                self.convertGridNode, (self.voxelGridResolution.x+7) / 8, (self.voxelGridResolution.y+7) / 8, (self.voxelGridResolution.z+7) / 8)

            # Generate the mipmaps
            self._generateMipmaps(self.voxelStableTex)

            self.helperLight.setPos(self.gridPos)
            self.helperLight.setDirection(direction)

            # We are done now, update the inputs
            self.ptaGridPos[0] = Vec3(self.gridPos)
            self._updateGridPos()
            

        self.frameIndex += 1
        self.frameIndex = self.frameIndex % 5


    def bindTo(self, node, prefix):
        """ Binds all required shader inputs to a target to compute / display
        the global illumination """

        normFactor = Vec3(
                1.0,
                float(self.voxelGridResolution.y) / float(self.voxelGridResolution.x) * self.voxelGridSizeWS.y / self.voxelGridSizeWS.x,
                float(self.voxelGridResolution.z) / float(self.voxelGridResolution.x) * self.voxelGridSizeWS.z / self.voxelGridSizeWS.x
            )
        node.setShaderInput(prefix + ".gridPos", self.ptaGridPos)
        node.setShaderInput(prefix + ".gridHalfSize", self.voxelGridSizeWS)
        node.setShaderInput(prefix + ".gridResolution", self.voxelGridResolution)
        node.setShaderInput(prefix + ".voxels", self.voxelStableTex)
        node.setShaderInput(prefix + ".voxelNormFactor", normFactor)
        node.setShaderInput(prefix + ".geometry", self.voxelStableTex)

    def _executeShader(self, node, threadsX, threadsY, threadsZ=1):
        """ Executes a compute shader, fetching the shader attribute from a NodePath """
        sattr = node.getAttrib(ShaderAttrib)
        Globals.base.graphicsEngine.dispatchCompute(
            (threadsX, threadsY, threadsZ), sattr, Globals.base.win.get_gsg())
