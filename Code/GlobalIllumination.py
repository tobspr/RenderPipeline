
from panda3d.core import Texture, NodePath, ShaderAttrib, Vec4, Vec3
from panda3d.core import Shader, SamplerState, GeomEnums
from panda3d.core import Vec2, LMatrix4f, LVecBase3i, Camera, Mat4
from panda3d.core import Mat4, OmniBoundingVolume, OrthographicLens
from panda3d.core import BoundingBox, Point3, CullFaceAttrib, PTAMat4
from panda3d.core import DepthTestAttrib, PTALVecBase3f, ComputeNode, PTALVecBase2f
from direct.stdpy.file import isfile, open, join

from Globals import Globals
from DebugObject import DebugObject
from LightType import LightType
from GUI.BufferViewerGUI import BufferViewerGUI
from RenderTarget import RenderTarget
from LightType import LightType
from SettingsManager import SettingsManager
from MemoryMonitor import MemoryMonitor
from DistributedTaskManager import DistributedTaskManager

from RenderPasses.GlobalIlluminationPass import GlobalIlluminationPass
from RenderPasses.VoxelizePass import VoxelizePass

import time
import math

class GlobalIllumination(DebugObject):

    """ This class handles the global illumination processing. To process the
    global illumination, the scene is first rasterized from 3 directions, and 
    a 3D voxel grid is created. After that, the mipmaps of the voxel grid are
    generated. The final shader then performs voxel cone tracing to compute 
    an ambient, diffuse and specular term.

    The gi is split over several frames to reduce the computation cost. Currently
    there are 5 different steps, split over 4 frames:

    Frame 1: 
        - Rasterize the scene from the x-axis

    Frame 2:
        - Rasterize the scene from the y-axis

    Frame 3: 
        - Rasterize the scene from the z-axis

    Frame 4:
        - Copy the generated temporary voxel grid into a stable voxel grid
        - Generate the mipmaps for that stable voxel grid using a gaussian filter

    In the final pass the stable voxel grid is sampled. The voxel tracing selects
    the mipmap depending on the cone size. This enables small scale details as well
    as blurry reflections and low-frequency ao / diffuse. For performance reasons,
    the final pass is executed at half window resolution and then bilateral upscaled.
    """


    def __init__(self, pipeline):
        DebugObject.__init__(self, "GlobalIllumnination")
        self.pipeline = pipeline

        # Grid size in world space units
        self.voxelGridSize = 80.0
        
        # Grid resolution in pixels
        self.voxelGridResolution = 128

        # Create the task manager
        self.taskManager = DistributedTaskManager()

        self.gridPosLive = PTALVecBase3f.emptyArray(1)
        self.gridPosTemp = PTALVecBase3f.emptyArray(1)

        self.frameIndex = 0
        self.steps = []

    def _createDebugTexts(self):
        """ Creates a debug overlay to show GI status """
        self.debugText = None

        try:
            from .GUI.FastText import FastText
            self.debugText = FastText(pos=Vec2(
                Globals.base.getAspectRatio() - 0.1, -0.84), rightAligned=True, color=Vec3(0, 1, 0), size=0.036)

        except Exception, msg:
            self.debug(
                "GI-Debug text is disabled because FastText wasn't loaded")

    def stepVoxelize(self, idx):
        
        # If we are at the beginning of the frame, compute the new grid position
        if idx == 0:
            self.gridPosTemp[0] = self._computeGridPos()

        self.voxelizePass.voxelizeSceneFromDirection(self.gridPosTemp[0], "xyz"[idx])
        self.debugText.setText("GI Grid Center: " + ", ".join(str(round(i, 2)) for i in self.gridPosTemp[0]) )

    def stepConvert(self, idx):
        # print "convert:", idx+1,"/",2 
        pass

    def stepMipmaps(self, idx):
        # print "mipmdps:", idx+1,"/", 4
        pass


    def update(self):
        """ Processes the gi, this method is called every frame """

        # TODO: Disable all buffers here
        self.voxelizePass.setActive(False)

        self.taskManager.process()


    def setup(self):
        """ Setups everything for the GI to work """

        self._createDebugTexts()


        self.taskManager.addTask(3, self.stepVoxelize)
        self.taskManager.addTask(2, self.stepConvert)
        self.taskManager.addTask(4, self.stepMipmaps)

        # Create the voxelize pass which is used to voxelize the scene from
        # several directions
        self.voxelizePass = VoxelizePass()
        self.voxelizePass.setVoxelGridResolution(self.voxelGridResolution)
        self.voxelizePass.setVoxelGridSize(self.voxelGridSize)
        self.voxelizePass.setGridResolutionMultiplier(1)
        self.pipeline.getRenderPassManager().registerPass(self.voxelizePass)

        # Create 3D Texture which is a copy of the voxel generation grid but
        # stable, as the generation grid is updated part by part and that would 
        # lead to flickering
        # self.voxelStableTex = Texture("VoxelsStable")
        # self.voxelStableTex.setup3dTexture(self.voxelGridResolution.x, self.voxelGridResolution.y, 
        #                                     self.voxelGridResolution.z, Texture.TFloat, Texture.FRgba8)

        # # Set appropriate filter types:
        # # The stable texture has mipmaps, which are generated during the process.
        # # This is required for cone tracing.
        # self.voxelStableTex.setMagfilter(SamplerState.FTLinear)
        # self.voxelStableTex.setMinfilter(SamplerState.FTLinear)
        # self.voxelStableTex.setWrapU(SamplerState.WMBorderColor)
        # self.voxelStableTex.setWrapV(SamplerState.WMBorderColor)
        # self.voxelStableTex.setWrapW(SamplerState.WMBorderColor)
        # self.voxelStableTex.setBorderColor(Vec4(0,0,0,0))
        # self.voxelStableTex.setClearColor(Vec4(0))
        # self.voxelStableTex.clearImage()

        # MemoryMonitor.addTexture("Voxel Grid Texture", self.voxelStableTex)

        # Create the various render targets to generate the mipmaps of the stable voxel grid
        # self.mipmapTargets = []
        # computeSize = LVecBase3i(self.voxelGridResolution)
        # currentMipmap = 0
        # while computeSize.z > 1:
        #     computeSize /= 2
        #     target = RenderTarget("GIMiplevel" + str(currentMipmap))
        #     target.setSize(computeSize.x, computeSize.y)
        #     target.setColorWrite(False)
        #     # target.addColorTexture()
        #     target.prepareOffscreenBuffer()
        #     target.setActive(False)
        #     target.setShaderInput("sourceMipmap", currentMipmap)
        #     target.setShaderInput("source", self.gatherStableTex)
        #     target.setShaderInput("dest", self.gatherStableTex, False, True, -1, currentMipmap + 1)
        #     self.mipmapTargets.append(target)
        #     currentMipmap += 1


        # Create the final gi pass
        # self.finalPass = GlobalIlluminationPass()
        # self.pipeline.getRenderPassManager().registerPass(self.finalPass)
        # self.pipeline.getRenderPassManager().registerDynamicVariable("giVoxelGridData", self.bindTo)



    def _createConvertShader(self):
        """ Loads the shader for converting the voxel grid """
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex", "Shader/GI/ConvertGrid.fragment")
        self.convertBuffer.setShader(shader)

        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex", "Shader/GI/ConvertPhotonGrid.fragment")
        self.gatherConvertBuffer.setShader(shader)

    def _createGenerateMipmapsShader(self):
        """ Loads the shader for generating the voxel grid mipmaps """
        computeSizeZ = self.voxelGridResolution.z
        for child in self.mipmapTargets:
            computeSizeZ /= 2
            shader = Shader.load(Shader.SLGLSL, 
                "Shader/DefaultPostProcess.vertex", 
                "Shader/GI/GenerateMipmaps/" + str(computeSizeZ) + ".fragment")
            child.setShader(shader)

    def _createDistributionShader(self):
        """ Creates the photon distribution shader """
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex", "Shader/GI/DistributePhotons.fragment")
        self.distributionPass.setShader(shader)

    def _createBlurShader(self):
        """ Creates the photon distribution shader """
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex", "Shader/GI/BlurPhotonGrid.fragment")
        self.blurBuffer.setShader(shader)

    def reloadShader(self):
        """ Reloads all shaders and updates the voxelization camera state aswell """
        # self._createGenerateMipmapsShader()
        # self._createConvertShader()
        # self._createPhotonBoxShader()
        # self._createDistributionShader()
        # self._createBlurShader()

        self.frameIndex = 0

    def _createPhotonBoxShader(self):
        """ Loads the shader to visualize the photons """
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultShaders/Photon/vertex.glsl",
            "Shader/DefaultShaders/Photon/fragment.glsl")
        # self.photonBox.setShader(shader, 100)

    def _computeGridPos(self):
        """ Computes the new center of the voxel grid. The center pos is also
        snapped, to avoid flickering. """

        # It is important that the grid is snapped, otherwise it will flicker 
        # while the camera moves. When using a snap of 32, everything until
        # the log2(32) = 5th mipmap is stable. 
        snap = 1.0
        stepSizeX = float(self.voxelGridSize * 2.0) / float(self.voxelGridResolution) * snap
        stepSizeY = float(self.voxelGridSize * 2.0) / float(self.voxelGridResolution) * snap
        stepSizeZ = float(self.voxelGridSize * 2.0) / float(self.voxelGridResolution) * snap

        gridPos = Globals.base.camera.getPos(Globals.base.render)
        gridPos.x -= gridPos.x % stepSizeX
        gridPos.y -= gridPos.y % stepSizeY
        gridPos.z -= gridPos.z % stepSizeZ
        return gridPos

    def bindTo(self, node, prefix):
        """ Binds all required shader inputs to a target to compute / display
        the global illumination """

        # normFactor = Vec3(1.0,
        #         float(self.voxelGridResolution.y) / float(self.voxelGridResolution.x) * self.voxelGridSizeWS.y / self.voxelGridSizeWS.x,
        #         float(self.voxelGridResolution.z) / float(self.voxelGridResolution.x) * self.voxelGridSizeWS.z / self.voxelGridSizeWS.x)
        # node.setShaderInput(prefix + ".gridPos", self.ptaGridPos)
        # node.setShaderInput(prefix + ".gridHalfSize", self.voxelGridSizeWS)
        # node.setShaderInput(prefix + ".gridResolution", self.voxelGridResolution)
        # node.setShaderInput(prefix + ".voxels", self.voxelStableTex)
        # node.setShaderInput(prefix + ".voxelNormFactor", normFactor)
        # node.setShaderInput(prefix + ".geometry", self.voxelStableTex)

