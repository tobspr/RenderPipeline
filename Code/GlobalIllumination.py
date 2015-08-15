
from panda3d.core import Texture, NodePath, ShaderAttrib, Vec4, Vec3
from panda3d.core import Shader, SamplerState, GeomEnums
from panda3d.core import Vec2, LMatrix4f, LVecBase3i, Camera, Mat4
from panda3d.core import Mat4, OmniBoundingVolume, OrthographicLens, PTAFloat
from panda3d.core import BoundingBox, Point3, CullFaceAttrib, PTAMat4, BoundingBox
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
from GUI.FastText import FastText

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

    QualityLevels = ["Low", "Medium", "High"]

    def __init__(self, pipeline):
        DebugObject.__init__(self, "GlobalIllumnination")
        self.pipeline = pipeline

        self.qualityLevel = self.pipeline.settings.giQualityLevel

        if self.qualityLevel not in self.QualityLevels:
            self.fatal("Unsupported gi quality level:" + self.qualityLevel)

        self.qualityLevelIndex = self.QualityLevels.index(self.qualityLevel)

        # Grid size in world space units
        self.voxelGridSize = self.pipeline.settings.giVoxelGridSize
        
        # Grid resolution in pixels
        self.voxelGridResolution = [32, 64, 128][self.qualityLevelIndex]

        # Has to be a multiple of 2
        self.distributionSteps = [16, 30, 60][self.qualityLevelIndex]
        self.slideCount = int(self.voxelGridResolution / 8) 
        self.slideVertCount = self.voxelGridResolution / self.slideCount       

        self.bounds = BoundingBox()
        self.renderCount = 0

        # Create the task manager
        self.taskManager = DistributedTaskManager()

        self.gridPosLive = PTALVecBase3f.emptyArray(1)
        self.gridPosTemp = PTALVecBase3f.emptyArray(1)

        # Store ready state
        self.readyStateFlag = PTAFloat.emptyArray(1)
        self.readyStateFlag[0] = 0

        self.frameIndex = 0
        self.steps = []

    def _createDebugTexts(self):
        """ Creates a debug overlay to show GI status """
        self.debugText = None
        self.buildingText = None

        if self.pipeline.settings.displayDebugStats:
            self.debugText = FastText(pos=Vec2(
                Globals.base.getAspectRatio() - 0.1, 0.88), rightAligned=True, color=Vec3(1, 1, 0), size=0.03)
            self.buildingText = FastText(pos=Vec2(-0.3, 0), rightAligned=False, color=Vec3(1, 1, 0), size=0.03)
            self.buildingText.setText("PREPARING GI, PLEASE BE PATIENT ....")

    def stepVoxelize(self, idx):
        
        # If we are at the beginning of the frame, compute the new grid position
        if idx == 0:
            self.gridPosTemp[0] = self._computeGridPos()
            # Clear voxel grid at the beginning
            # for tex in self.generationTextures:
                # tex.clearImage()

            self.clearGridTarget.setActive(True)

            if self.debugText is not None:
                self.debugText.setText("GI Grid Center: " + ", ".join(str(round(i, 2)) for i in self.gridPosTemp[0]) + " / GI Frame " + str(self.renderCount) )
            
            self.renderCount += 1

            if self.renderCount == 3:
                self.readyStateFlag[0] = 1.0
                if self.buildingText:
                    self.buildingText.remove()
                    self.buildingText = None

        self.voxelizePass.voxelizeSceneFromDirection(self.gridPosTemp[0], "xyz"[idx])


    def stepDistribute(self, idx):
        
        if idx == 0:

            skyBegin = 142.0
            skyInGrid = (skyBegin - self.gridPosTemp[0].z) / (2.0 * self.voxelGridSize)
            skyInGrid = int(skyInGrid * self.voxelGridResolution)
            self.convertGridTarget.setShaderInput("skyStartZ", skyInGrid)
            self.convertGridTarget.setActive(True)           

        self.distributeTarget.setActive(True)

        swap = idx % 2 == 0
        sources = self.pingDataTextures if swap else self.pongDataTextures
        dests = self.pongDataTextures if swap else self.pingDataTextures

        if idx == self.distributionSteps - 1:
            self.publishGrid()
            dests = self.dataTextures

        for i in xrange(5):
            self.distributeTarget.setShaderInput("src" + str(i), sources[i])
            self.distributeTarget.setShaderInput("dst" + str(i), dests[i])

        self.distributeTarget.setShaderInput("isLastStep", idx >= self.distributionSteps-1)

    def publishGrid(self):
        """ This function gets called when the grid is ready to be used, and updates
        the live grid data """
        self.gridPosLive[0] = self.gridPosTemp[0]
        self.bounds.setMinMax(self.gridPosLive[0]-Vec3(self.voxelGridSize), self.gridPosLive[0]+Vec3(self.voxelGridSize))

    def getBounds(self):
        """ Returns the bounds of the gi grid """
        return self.bounds

    def update(self):
        """ Processes the gi, this method is called every frame """

        # Disable all buffers here before starting the rendering
        self.disableTargets()
        # for target in self.mipmapTargets:
            # target.setActive(False)

        self.taskManager.process()

    def disableTargets(self):
        """ Disables all active targets """
        self.voxelizePass.setActive(False)
        self.convertGridTarget.setActive(False)
        self.clearGridTarget.setActive(False)
        self.distributeTarget.setActive(False)


    def setup(self):
        """ Setups everything for the GI to work """

        assert(self.voxelGridResolution in [16, 32, 64, 128, 256, 512])
        assert(self.distributionSteps % 2 == 0)

        self._createDebugTexts()

        self.pipeline.getRenderPassManager().registerDefine("USE_GLOBAL_ILLUMINATION", 1)
        self.pipeline.getRenderPassManager().registerDefine("GI_SLIDE_COUNT", self.slideCount)
        self.pipeline.getRenderPassManager().registerDefine("GI_QUALITY_LEVEL", self.qualityLevelIndex)

        # make the grid resolution a constant
        self.pipeline.getRenderPassManager().registerDefine("GI_GRID_RESOLUTION", self.voxelGridResolution)

        self.taskManager.addTask(3, self.stepVoxelize)
        self.taskManager.addTask(self.distributionSteps, self.stepDistribute)

        # Create the voxelize pass which is used to voxelize the scene from
        # several directions
        self.voxelizePass = VoxelizePass(self.pipeline)
        self.voxelizePass.setVoxelGridResolution(self.voxelGridResolution)
        self.voxelizePass.setVoxelGridSize(self.voxelGridSize)
        self.voxelizePass.setGridResolutionMultiplier(1)
        self.pipeline.getRenderPassManager().registerPass(self.voxelizePass)

        self.generationTextures = []

        # Create the buffers used to create the voxel grid
        for color in "rgb":
            tex = Texture("VoxelGeneration-" + color)
            tex.setup3dTexture(self.voxelGridResolution, self.voxelGridResolution, self.voxelGridResolution, Texture.TInt, Texture.FR32)
            tex.setClearColor(Vec4(0))
            self.generationTextures.append(tex)
            Globals.render.setShaderInput("voxelGenDest" + color.upper(), tex)
            
            MemoryMonitor.addTexture("VoxelGenerationTex-" + color.upper(), tex)

        self.bindTo(Globals.render, "giData")

        self.convertGridTarget = RenderTarget("ConvertGIGrid")
        self.convertGridTarget.setSize(self.voxelGridResolution * self.slideCount, self.voxelGridResolution * self.slideVertCount)

        if self.pipeline.settings.useDebugAttachments:
            self.convertGridTarget.addColorTexture()
        self.convertGridTarget.prepareOffscreenBuffer()

        # Set a near-filter to the texture
        if self.pipeline.settings.useDebugAttachments:
            self.convertGridTarget.getColorTexture().setMinfilter(Texture.FTNearest)
            self.convertGridTarget.getColorTexture().setMagfilter(Texture.FTNearest)

        self.clearGridTarget = RenderTarget("ClearGIGrid")
        self.clearGridTarget.setSize(self.voxelGridResolution * self.slideCount, self.voxelGridResolution * self.slideVertCount)
        if self.pipeline.settings.useDebugAttachments:
            self.clearGridTarget.addColorTexture()
        self.clearGridTarget.prepareOffscreenBuffer()

        for idx, color in enumerate("rgb"):
            self.convertGridTarget.setShaderInput("voxelGenSrc" + color.upper(), self.generationTextures[idx])
            self.clearGridTarget.setShaderInput("voxelGenTex" + color.upper(), self.generationTextures[idx])


        # Create the data textures
        self.dataTextures = []


        for i in xrange(5):
            tex = Texture("GIDataTex" + str(i))
            tex.setup3dTexture(self.voxelGridResolution, self.voxelGridResolution, self.voxelGridResolution, Texture.TFloat, Texture.FRgba16)
            MemoryMonitor.addTexture("VoxelDataTex-" + str(i), tex)
           
            self.dataTextures.append(tex)
            self.pipeline.getRenderPassManager().registerStaticVariable("giVoxelData" + str(i), tex)

        self.pingDataTextures = []
        self.pongDataTextures = []

        for i in xrange(5):
            texPing = Texture("GIPingDataTex" + str(i))
            texPing.setup3dTexture(self.voxelGridResolution, self.voxelGridResolution, self.voxelGridResolution, Texture.TFloat, Texture.FRgba16)
            MemoryMonitor.addTexture("VoxelPingDataTex-" + str(i), texPing)
            self.pingDataTextures.append(texPing)

            texPong = Texture("GIPongDataTex" + str(i))
            texPong.setup3dTexture(self.voxelGridResolution, self.voxelGridResolution, self.voxelGridResolution, Texture.TFloat, Texture.FRgba16)
            MemoryMonitor.addTexture("VoxelPongDataTex-" + str(i), texPong)
            self.pongDataTextures.append(texPong)

            self.convertGridTarget.setShaderInput("voxelDataDest"+str(i), self.pingDataTextures[i])
            # self.clearGridTarget.setShaderInput("voxelDataDest" + str(i), self.pongDataTextures[i])
        
        # Set texture wrap modes
        for tex in self.pingDataTextures + self.pongDataTextures + self.dataTextures + self.generationTextures:
            tex.setMinfilter(Texture.FTLinear)
            tex.setMagfilter(Texture.FTLinear)
            tex.setWrapU(Texture.WMBorderColor)
            tex.setWrapV(Texture.WMBorderColor)
            tex.setWrapW(Texture.WMBorderColor)
            tex.setBorderColor(Vec4(0))

        for tex in self.dataTextures:
            tex.setMinfilter(Texture.FTLinear)
            tex.setMagfilter(Texture.FTLinear)

        self.distributeTarget = RenderTarget("DistributeVoxels")
        self.distributeTarget.setSize(self.voxelGridResolution * self.slideCount, self.voxelGridResolution * self.slideVertCount)

        if self.pipeline.settings.useDebugAttachments:
            self.distributeTarget.addColorTexture()
        self.distributeTarget.prepareOffscreenBuffer()

        # Set a near-filter to the texture
        if self.pipeline.settings.useDebugAttachments:
            self.distributeTarget.getColorTexture().setMinfilter(Texture.FTNearest)
            self.distributeTarget.getColorTexture().setMagfilter(Texture.FTNearest)


        # Create the various render targets to generate the mipmaps of the stable voxel grid
        # self.mipmapTargets = []
        # computeSize = self.voxelGridResolution
        # currentMipmap = 0
        # while computeSize > 1:
        #     computeSize /= 2
        #     target = RenderTarget("GIMipLevel" + str(currentMipmap))
        #     target.setSize(computeSize, computeSize)
        #     # target.setColorWrite(False)
        #     target.addColorTexture()
        #     target.prepareOffscreenBuffer()
        #     target.setActive(False)
        #     target.setShaderInput("sourceMipmap", currentMipmap)

        #     for i in xrange(5):
        #         target.setShaderInput("source" + str(i), self.dataTextures[i])
        #         target.setShaderInput("dest" + str(i), self.dataTextures[i], False, True, -1, currentMipmap + 1)
        #     self.mipmapTargets.append(target)
        #     currentMipmap += 1


        # Create the final gi pass
        self.finalPass = GlobalIlluminationPass()
        self.pipeline.getRenderPassManager().registerPass(self.finalPass)
        self.pipeline.getRenderPassManager().registerDynamicVariable("giData", self.bindTo)
        self.pipeline.getRenderPassManager().registerStaticVariable("giReadyState", self.readyStateFlag)


        # Visualize voxels
        if False:
            self.voxelCube = loader.loadModel("Box")
            self.voxelCube.reparentTo(render)
            # self.voxelCube.setTwoSided(True)
            self.voxelCube.node().setFinal(True)
            self.voxelCube.node().setBounds(OmniBoundingVolume())
            self.voxelCube.setInstanceCount(self.voxelGridResolution**3)
            # self.voxelCube.hide()
            self.bindTo(self.voxelCube, "giData")
            
            for i in xrange(5):
                self.voxelCube.setShaderInput("giDataTex" + str(i), self.pingDataTextures[i])

        self.disableTargets()

    def _createConvertShader(self):
        """ Loads the shader for converting the voxel grid """
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex", "Shader/GI/ConvertGrid.fragment")
        self.convertGridTarget.setShader(shader)

    def _createClearShader(self):
        """ Loads the shader for converting the voxel grid """
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex", "Shader/GI/ClearGrid.fragment")
        self.clearGridTarget.setShader(shader)

    def _createGenerateMipmapsShader(self):
        """ Loads the shader for generating the voxel grid mipmaps """
        computeSize = self.voxelGridResolution
        for child in self.mipmapTargets:
            computeSize /= 2
            shader = Shader.load(Shader.SLGLSL, 
                "Shader/DefaultPostProcess.vertex", 
                "Shader/GI/GenerateMipmaps/" + str(computeSize) + ".fragment")
            child.setShader(shader)

    def _createDistributionShader(self):
        """ Creates the photon distribution shader """
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex", "Shader/GI/Distribute.fragment")
        self.distributeTarget.setShader(shader)

    def _createBlurShader(self):
        """ Creates the photon distribution shader """
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex", "Shader/GI/BlurPhotonGrid.fragment")
        self.blurBuffer.setShader(shader)

    def reloadShader(self):
        """ Reloads all shaders and updates the voxelization camera state aswell """
        self.debug("Reloading shaders")
        self._createConvertShader()
        self._createClearShader()
        self._createDistributionShader()
        # self._createGenerateMipmapsShader()
        # self._createPhotonBoxShader()
        # self._createBlurShader()

        if hasattr(self, "voxelCube"):
            self.pipeline.setEffect(self.voxelCube, "Effects/DisplayVoxels.effect", {
                "normalMapping": False,
                "castShadows": False,
                "castGI": False
            })

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

        node.setShaderInput(prefix + ".positionGeneration", self.gridPosTemp)
        node.setShaderInput(prefix + ".position", self.gridPosLive)
        node.setShaderInput(prefix + ".size", self.voxelGridSize)
        node.setShaderInput(prefix + ".resolution", self.voxelGridResolution)