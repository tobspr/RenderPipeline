
from panda3d.core import Texture, NodePath, ShaderAttrib, Vec4, Vec3
from panda3d.core import Shader, SamplerState
from panda3d.core import Vec2, LMatrix4f, LVecBase3i, Camera, Mat4
from panda3d.core import Mat4, OmniBoundingVolume, OrthographicLens
from panda3d.core import BoundingBox, Point3, CullFaceAttrib
from panda3d.core import DepthTestAttrib, PTALVecBase3f, ComputeNode
from direct.stdpy.file import isfile, open, join

from Globals import Globals
from DebugObject import DebugObject
from LightType import LightType
from GUI.BufferViewerGUI import BufferViewerGUI
from RenderTarget import RenderTarget
from GIHelperLight import GIHelperLight
from LightType import LightType
from SettingsManager import SettingsManager
from MemoryMonitor import MemoryMonitor

import time
import math

class GlobalIllumination(DebugObject):

    """ This class handles the global illumination processing. It is still
    experimental, and thus not commented. """

    updateEnabled = False

    def __init__(self, pipeline):
        DebugObject.__init__(self, "GlobalIllumnination")
        self.pipeline = pipeline

        # Fetch the scene data
        self.targetCamera = Globals.base.cam
        self.targetSpace = Globals.base.render

        # Store grid size in world space units
        self.voxelGridSizeWS = Vec3(55)

        # Store grid resolution, should be equal for each dimension

        # When you change this resolution, you have to change it in Shader/GI/ConvertGrid.fragment aswell
        self.voxelGridResolution = LVecBase3i(256)
        self.voxelBaseResolution = self.voxelGridResolution.x * 4
        self.targetLight = None
        self.helperLight = None
        self.ptaGridPos = PTALVecBase3f.emptyArray(1)
        self.gridPos = Vec3(0)

    @classmethod
    def setUpdateEnabled(self, enabled):
        self.updateEnabled = enabled

    def setTargetLight(self, light):
        """ Sets the sun light which is the main source of GI. Only that light
        casts gi. """

        if light._getLightType() != LightType.Directional:
            self.error("setTargetLight expects a directional light!")
            return

        self.targetLight = light
        self._createHelperLight()

    def _prepareVoxelScene(self):
        """ Creates the internal buffer to voxelize the scene on the fly """

        self.voxelizeScene = Globals.render

        # Create voxelize camera
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

        # Create voxelize target
        self.voxelizeTarget = RenderTarget("DynamicVoxelization")
        self.voxelizeTarget.setSize(self.voxelBaseResolution) 
        self.voxelizeTarget.setColorWrite(False)
        # self.voxelizeTarget.addColorTexture()
        self.voxelizeTarget.setSource(self.voxelizeCameraNode, Globals.base.win)
        self.voxelizeTarget.prepareSceneRender()

        self.voxelizeTarget.getQuad().node().removeAllChildren()
        self.voxelizeTarget.getInternalRegion().setSort(-400)
        self.voxelizeTarget.getInternalBuffer().setSort(-399)

        # Set required inputs to create the voxel grid
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
        self.voxelizeShader = Shader.load(Shader.SLGLSL, 
            "Shader/GI/Voxelize.vertex",
            "Shader/GI/Voxelize.fragment")

        # Create tag state
        initialState = NodePath("VoxelizerState")
        initialState.setShader(self.voxelizeShader, 500)
        initialState.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullNone))
        initialState.setDepthWrite(False)
        initialState.setDepthTest(False)
        initialState.setAttrib(DepthTestAttrib.make(DepthTestAttrib.MNone))
        initialState.setShaderInput("dv_dest_tex", self.voxelGenTex)

        # Apply tag state
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

        self._prepareVoxelScene()

        # Create 3D Texture to store the voxel generation grid
        self.voxelGenTex = Texture("VoxelsTemp")
        self.voxelGenTex.setup3dTexture(self.voxelGridResolution.x, self.voxelGridResolution.y, 
                                        self.voxelGridResolution.z, Texture.TInt, Texture.FR32i)

        # Set appropriate filter types
        self.voxelGenTex.setMinfilter(SamplerState.FTNearest)
        self.voxelGenTex.setMagfilter(Texture.FTNearest)
        self.voxelGenTex.setWrapU(Texture.WMClamp)
        self.voxelGenTex.setWrapV(Texture.WMClamp)
        self.voxelGenTex.setWrapW(Texture.WMClamp)
        self.voxelGenTex.setClearColor(Vec4(0))


        MemoryMonitor.addTexture("Voxel Temp Texture", self.voxelGenTex)

        # Create 3D Texture which is a copy of the voxel generation grid but
        # stable, as the generation grid is updated part by part and that would 
        # lead to flickering
        self.voxelStableTex = Texture("VoxelsStable")
        self.voxelStableTex.setup3dTexture(self.voxelGridResolution.x, self.voxelGridResolution.y, 
                                            self.voxelGridResolution.z, Texture.TFloat, Texture.FRgba8)

        # Set appropriate filter types:
        # The stable texture has mipmaps, which are generated during the process.
        # This is required for cone tracing.
        self.voxelStableTex.setMagfilter(SamplerState.FTLinear)
        self.voxelStableTex.setMinfilter(SamplerState.FTLinearMipmapLinear)
        self.voxelStableTex.setWrapU(SamplerState.WMBorderColor)
        self.voxelStableTex.setWrapV(SamplerState.WMBorderColor)
        self.voxelStableTex.setWrapW(SamplerState.WMBorderColor)
        self.voxelStableTex.setBorderColor(Vec4(0,0,0,0))

        MemoryMonitor.addTexture("Voxel Grid Texture", self.voxelStableTex)

        # Setups the render target to convert the voxel grid
        self.convertBuffer = RenderTarget("VoxelConvertBuffer")
        self.convertBuffer.setSize(self.voxelGridResolution.x, self.voxelGridResolution.y)
        self.convertBuffer.setColorWrite(False)
        # self.convertBuffer.addColorTexture()
        self.convertBuffer.prepareOffscreenBuffer()
        self.convertBuffer.setShaderInput("src", self.voxelGenTex)
        self.convertBuffer.setShaderInput("dest", self.voxelStableTex)
        self.convertBuffer.setActive(False)

        # Store the frame index, we need that to decide which step we are currently
        # doing
        self.frameIndex = 0

        # Create the nodes which generate the voxel mipmaps
        # self.mipmapNodes = self.computeNodes.attachNewNode("GenerateMipmaps")
        # self.mipmapNodes.setBin("fixed", 15)
        # self.mipmapNodes.hide()

        self.mipmapTargets = []
        computeSize = LVecBase3i(self.voxelGridResolution)
        currentMipmap = 0
        while computeSize.z > 1:
            computeSize /= 2
            target = RenderTarget("GIMiplevel" + str(currentMipmap))
            target.setSize(computeSize.x, computeSize.y)
            target.setColorWrite(False)
            # target.addColorTexture()
            target.prepareOffscreenBuffer()
            target.setActive(False)
            target.setShaderInput("sourceMipmap", currentMipmap)
            target.setShaderInput("source", self.voxelStableTex)
            target.setShaderInput("dest", self.voxelStableTex, False, True, -1, currentMipmap + 1)
            self.mipmapTargets.append(target)
            currentMipmap += 1


    def _createConvertShader(self):
        """ Loads the shader for converting the voxel grid """
        shader = Shader.load(Shader.SLGLSL, "Shader/DefaultPostProcess.vertex", "Shader/GI/ConvertGrid.fragment")
        self.convertBuffer.setShader(shader)

    def _createGenerateMipmapsShader(self):
        """ Loads the shader for generating the voxel grid mipmaps """

        computeSizeZ = self.voxelGridResolution.z
        for child in self.mipmapTargets:
            computeSizeZ /= 2
            shader = Shader.load(Shader.SLGLSL, "Shader/DefaultPostProcess.vertex", "Shader/GI/GenerateMipmaps/" + str(computeSizeZ) + ".fragment")
            child.setShader(shader)

    def reloadShader(self):
        """ Reloads all shaders and updates the voxelization camera state aswell """
        self._createGenerateMipmapsShader()
        self._createConvertShader()
        self._createVoxelizeState()

    def _updateGridPos(self):
        """ Computes the new center of the grid """

        # It is important that the grid is snapped, otherwise it will flicker 
        # while the camera moves. When using a snap of 32, everything until
        # the log2(32) = 5th mipmap is stable. 
        snap = 32.0
        stepSizeX = float(self.voxelGridSizeWS.x * 2.0) / float(self.voxelGridResolution.x) * snap
        stepSizeY = float(self.voxelGridSizeWS.y * 2.0) / float(self.voxelGridResolution.y) * snap
        stepSizeZ = float(self.voxelGridSizeWS.z * 2.0) / float(self.voxelGridResolution.z) * snap

        self.gridPos = self.targetCamera.getPos(self.targetSpace)
        self.gridPos.x -= self.gridPos.x % stepSizeX
        self.gridPos.y -= self.gridPos.y % stepSizeY
        self.gridPos.z -= self.gridPos.z % stepSizeZ

    def process(self):
        """ Processes the gi, this method is called every frame """

        # TODO: Make gi work with all light types

        # With no light, there is no gi
        if self.targetLight is None:
            self.fatal("The GI cannot work without a directional target light! Set one "
                "with renderPipeline.setGILightSource(directionalLight) first!")


        # When the gi is disabled by the gui manager, don't do anything at all
        if not self.updateEnabled:
            self.voxelizeTarget.setActive(False)
            return


        # Fetch current light direction
        direction = self.targetLight.getDirection()

        if self.frameIndex == 0:
            # Step 1: Voxelize scene from the x-Axis
            self.targetSpace.setShaderInput("dv_uv_start", 
                self.helperLight.shadowSources[0].getAtlasPos())

            for child in self.mipmapTargets:
                child.setActive(False)
            self.convertBuffer.setActive(False)

            # Clear the old data in generation texture 
            self.voxelGenTex.clearImage()
            self.voxelizeTarget.setActive(True)
            self.voxelizeLens.setFilmSize(self.voxelGridSizeWS.y*2, self.voxelGridSizeWS.z*2)
            self.voxelizeLens.setNearFar(0.0, self.voxelGridSizeWS.x*2)

            self.targetSpace.setShaderInput("dv_mvp", Mat4(self.helperLight.shadowSources[0].mvp))
            self.targetSpace.setShaderInput("dv_gridStart", self.gridPos - self.voxelGridSizeWS)
            self.targetSpace.setShaderInput("dv_gridEnd", self.gridPos + self.voxelGridSizeWS)
            self.targetSpace.setShaderInput("dv_lightdir", direction)

            self.voxelizeCameraNode.setPos(self.gridPos - Vec3(self.voxelGridSizeWS.x, 0, 0))
            self.voxelizeCameraNode.lookAt(self.gridPos)
            self.targetSpace.setShaderInput("dv_direction", 0)

        elif self.frameIndex == 1:

            # Step 2: Voxelize scene from the y-Axis
            self.voxelizeLens.setFilmSize(self.voxelGridSizeWS.x*2, self.voxelGridSizeWS.z*2)
            self.voxelizeLens.setNearFar(0.0, self.voxelGridSizeWS.y*2)
            self.voxelizeCameraNode.setPos(self.gridPos - Vec3(0, self.voxelGridSizeWS.y, 0))
            self.voxelizeCameraNode.lookAt(self.gridPos)
            self.targetSpace.setShaderInput("dv_direction", 1)

        elif self.frameIndex == 2:

            # Step 3: Voxelize the scene from the z-Axis 
            self.voxelizeLens.setFilmSize(self.voxelGridSizeWS.x*2, self.voxelGridSizeWS.y*2)
            self.voxelizeLens.setNearFar(0.0, self.voxelGridSizeWS.z*2)
            self.voxelizeCameraNode.setPos(self.gridPos + Vec3(0, 0, self.voxelGridSizeWS.z))
            self.voxelizeCameraNode.lookAt(self.gridPos)
            self.targetSpace.setShaderInput("dv_direction", 2)
            
            # Update helper light, so that it is at the right position when Step 1
            # starts again 
            self.helperLight.setPos(self.gridPos)
            self.helperLight.setDirection(direction)

        elif self.frameIndex == 3:

            # Step 4: Extract voxel grid and generate mipmaps
            self.voxelizeTarget.setActive(False)
            self.convertBuffer.setActive(True)

            for child in self.mipmapTargets:
                child.setActive(True)

            # We are done now, update the inputs
            self.ptaGridPos[0] = Vec3(self.gridPos)
            self._updateGridPos()

        # Increase frame index
        self.frameIndex += 1
        self.frameIndex = self.frameIndex % 4

    def bindTo(self, node, prefix):
        """ Binds all required shader inputs to a target to compute / display
        the global illumination """

        normFactor = Vec3(1.0,
                float(self.voxelGridResolution.y) / float(self.voxelGridResolution.x) * self.voxelGridSizeWS.y / self.voxelGridSizeWS.x,
                float(self.voxelGridResolution.z) / float(self.voxelGridResolution.x) * self.voxelGridSizeWS.z / self.voxelGridSizeWS.x)
        node.setShaderInput(prefix + ".gridPos", self.ptaGridPos)
        node.setShaderInput(prefix + ".gridHalfSize", self.voxelGridSizeWS)
        node.setShaderInput(prefix + ".gridResolution", self.voxelGridResolution)
        node.setShaderInput(prefix + ".voxels", self.voxelStableTex)
        node.setShaderInput(prefix + ".voxelNormFactor", normFactor)
        node.setShaderInput(prefix + ".geometry", self.voxelStableTex)

