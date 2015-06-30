
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
from GIHelperLight import GIHelperLight
from LightType import LightType
from SettingsManager import SettingsManager
from MemoryMonitor import MemoryMonitor

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

        # Fetch the scene data
        self.targetCamera = Globals.base.cam
        self.targetSpace = Globals.base.render

        # Store grid size in world space units
        # This is the half voxel grid size
        self.voxelGridSizeWS = Vec3(40)

        # When you change this resolution, you have to change it in Shader/GI/ConvertGrid.fragment aswell
        self.voxelGridResolution = LVecBase3i(256)

        self.targetLight = None
        self.helperLight = None
        self.ptaGridPos = PTALVecBase3f.emptyArray(1)
        self.gridPos = Vec3(0)

        self.distributionPassCount = 32
        self.photonScaleFactor = 1
        self.photonBaseSize = 256

        # Create ptas 
        self.ptaLightUVStart = PTALVecBase2f.emptyArray(1)
        self.ptaLightMVP = PTAMat4.emptyArray(1)
        self.ptaVoxelGridStart = PTALVecBase3f.emptyArray(1)
        self.ptaVoxelGridEnd = PTALVecBase3f.emptyArray(1)
        self.ptaLightDirection = PTALVecBase3f.emptyArray(1)

        self.targetSpace.setShaderInput("giLightUVStart", self.ptaLightUVStart)
        self.targetSpace.setShaderInput("giLightMVP", self.ptaLightMVP)
        self.targetSpace.setShaderInput("giVoxelGridStart", self.ptaVoxelGridStart)
        self.targetSpace.setShaderInput("giVoxelGridEnd", self.ptaVoxelGridEnd)
        self.targetSpace.setShaderInput("giLightDirection", self.ptaLightDirection)

    def setTargetLight(self, light):
        """ Sets the sun light which is the main source of GI. Only that light
        casts gi. """
        if light.getLightType() != LightType.Directional:
            self.error("setTargetLight expects a directional light!")
            return

        self.targetLight = light
        self._createHelperLight()

    def _createHelperLight(self):
        """ Creates the helper light. We can't use the main directional light
        because it uses PSSM, so we need an extra shadow map that covers the
        whole voxel grid. """
        self.helperLight = GIHelperLight()
        self.helperLight.setPos(Vec3(50,50,100))
        self.helperLight.setShadowMapResolution(512)
        self.helperLight.setFilmSize(math.sqrt( (self.voxelGridSizeWS.x**2) * 4) )
        # self.helperLight.setFilmSize()
        self.helperLight.setCastsShadows(True)
        self.pipeline.addLight(self.helperLight)
        self.targetSpace.setShaderInput("giLightUVSize", 
            float(self.helperLight.shadowResolution) / self.pipeline.settings.shadowAtlasSize)
        self._updateGridPos()

    def _createDebugTexts(self):
        """ Creates a debug overlay to show GI status """
        self.debugText = None


        try:
            from Code.GUI.FastText import FastText
            self.debugText = FastText(pos=Vec2(
                Globals.base.getAspectRatio() - 0.1, -0.84), rightAligned=True, color=Vec3(0, 1, 0), size=0.036)

        except Exception, msg:
            self.debug(
                "GI-Debug text is disabled because FastText wasn't loaded")

    def setup(self):
        """ Setups everything for the GI to work """

        # Create the voxelize pass which is used to voxelize the scene from
        # several directions
        self.voxelizePass = VoxelizePass()
        self.voxelizePass.setVoxelGridResolution(self.voxelGridResolution)
        self.voxelizePass.setVoxelGridSize(self.voxelGridSizeWS)
        self.voxelizePass.setPhotonScaleFactor(self.photonScaleFactor)
        self.voxelizePass.initVoxelStorage()
        self.pipeline.getRenderPassManager().registerPass(self.voxelizePass)

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
        self.voxelStableTex.setMinfilter(SamplerState.FTLinear)
        self.voxelStableTex.setWrapU(SamplerState.WMBorderColor)
        self.voxelStableTex.setWrapV(SamplerState.WMBorderColor)
        self.voxelStableTex.setWrapW(SamplerState.WMBorderColor)
        self.voxelStableTex.setBorderColor(Vec4(0,0,0,0))
        self.voxelStableTex.setClearColor(Vec4(0))
        self.voxelStableTex.clearImage()

        MemoryMonitor.addTexture("Voxel Grid Texture", self.voxelStableTex)



        # Setups the render target to convert the voxel grid
        self.convertBuffer = RenderTarget("VoxelConvertBuffer")
        self.convertBuffer.setSize(self.voxelGridResolution.x, self.voxelGridResolution.y)
        self.convertBuffer.setColorWrite(False)
        self.convertBuffer.addColorTexture()
        self.convertBuffer.prepareOffscreenBuffer()
        self.convertBuffer.setShaderInput("src", self.voxelizePass.getVoxelTex())
        self.convertBuffer.setShaderInput("dest", self.voxelStableTex)
        self.convertBuffer.setActive(False)

        # Create 3D Texture which is a copy of the voxel generation grid but
        # stable, as the generation grid is updated part by part and that would 
        # lead to flickering
        self.gatherStableTex = Texture("GatherStable")
        self.gatherStableTex.setup3dTexture(self.voxelGridResolution.x, self.voxelGridResolution.y, 
                                            self.voxelGridResolution.z, Texture.TFloat, Texture.FRgba16)

        # Set appropriate filter types:
        # The stable texture has mipmaps, which are generated during the process.
        # This is required for cone tracing.
        self.gatherStableTex.setMagfilter(SamplerState.FTLinear)
        self.gatherStableTex.setMinfilter(SamplerState.FTLinear)
        # self.gatherStableTex.setMinfilter(SamplerState.FTLinear)
        self.gatherStableTex.setWrapU(SamplerState.WMBorderColor)
        self.gatherStableTex.setWrapV(SamplerState.WMBorderColor)
        self.gatherStableTex.setWrapW(SamplerState.WMBorderColor)
        self.gatherStableTex.setBorderColor(Vec4(0,0,0,0))
        self.gatherStableTex.setClearColor(Vec4(0))
        self.gatherStableTex.clearImage()


        MemoryMonitor.addTexture("Gather Stable Texture", self.gatherStableTex)


        # Create 3D Texture which is a copy of the voxel generation grid but
        # stable, as the generation grid is updated part by part and that would 
        # lead to flickering
        self.gatherStablePongTex = Texture("GatherStablePong")
        self.gatherStablePongTex.setup3dTexture(self.voxelGridResolution.x, self.voxelGridResolution.y, 
                                            self.voxelGridResolution.z, Texture.TFloat, Texture.FRgba16)

        # Set appropriate filter types:
        # The stable texture has mipmaps, which are generated during the process.
        # This is required for cone tracing.
        self.gatherStablePongTex.setMagfilter(SamplerState.FTLinear)
        self.gatherStablePongTex.setMinfilter(SamplerState.FTLinear)
        # self.gatherStableTex.setMinfilter(SamplerState.FTLinear)
        self.gatherStablePongTex.setWrapU(SamplerState.WMBorderColor)
        self.gatherStablePongTex.setWrapV(SamplerState.WMBorderColor)
        self.gatherStablePongTex.setWrapW(SamplerState.WMBorderColor)
        self.gatherStablePongTex.setBorderColor(Vec4(0,0,0,0))
        self.gatherStablePongTex.setClearColor(Vec4(0))
        self.gatherStablePongTex.clearImage()

        MemoryMonitor.addTexture("Gather Stable Texture - Pong", self.gatherStablePongTex)


        # Create 3D Texture which is a copy of the voxel generation grid but
        # stable, as the generation grid is updated part by part and that would 
        # lead to flickering
        self.gatherStablePingTex = Texture("GatherStablePing")
        self.gatherStablePingTex.setup3dTexture(self.voxelGridResolution.x, self.voxelGridResolution.y, 
                                            self.voxelGridResolution.z, Texture.TFloat, Texture.FRgba16)

        # Set appropriate filter types:
        # The stable texture has mipmaps, which are generated during the process.
        # This is required for cone tracing.
        self.gatherStablePingTex.setMagfilter(SamplerState.FTLinear)
        self.gatherStablePingTex.setMinfilter(SamplerState.FTLinear)
        # selgatherStablePingTexetMinfilter(SamplerState.FTLinear)
        self.gatherStablePingTex.setWrapU(SamplerState.WMBorderColor)
        self.gatherStablePingTex.setWrapV(SamplerState.WMBorderColor)
        self.gatherStablePingTex.setWrapW(SamplerState.WMBorderColor)
        self.gatherStablePingTex.setBorderColor(Vec4(0,0,0,0))
        self.gatherStablePingTex.setClearColor(Vec4(0))
        self.gatherStablePingTex.clearImage()

        MemoryMonitor.addTexture("Gather Stable Texture - Ping", self.gatherStablePingTex)




        # Store the frame index, we need that to decide which step we are currently
        # doing
        self.frameIndex = 0

        # Create the various render targets to generate the mipmaps of the stable voxel grid
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
            target.setShaderInput("source", self.gatherStableTex)
            target.setShaderInput("dest", self.gatherStableTex, False, True, -1, currentMipmap + 1)
            self.mipmapTargets.append(target)
            currentMipmap += 1


        # Create the final gi pass
        self.finalPass = GlobalIlluminationPass()
        self.pipeline.getRenderPassManager().registerPass(self.finalPass)
        self.pipeline.getRenderPassManager().registerDynamicVariable("giVoxelGridData", self.bindTo)

        # Create the photon buffer
        
        maxPhotons = self.photonBaseSize * self.photonBaseSize

        self.photonBuffer = Texture("Photons")
        self.photonBuffer.setupBufferTexture(maxPhotons*3, Texture.TFloat, Texture.FRgba16, GeomEnums.UHStatic)
        self.photonBuffer.setClearColor(Vec4(0))
        self.photonBuffer.clearImage()

        MemoryMonitor.addTexture("Photon Buffer", self.photonBuffer)

        # Create the photon counter
        self.photonCounter = Texture("PhotonCounter")
        self.photonCounter.setup2dTexture(1, 1, Texture.TInt, Texture.FR32i)
        self.photonCounter.setClearColor(Vec4(0))
        self.photonCounter.clearImage()

        MemoryMonitor.addTexture("Photon Counter", self.photonCounter)


        # Create the gather buffers
        self.gatherGridBuffer0 = Texture("GatherGrid0")
        self.gatherGridBuffer0.setup3dTexture(self.voxelGridResolution.x, self.voxelGridResolution.y, 
                                            self.voxelGridResolution.z, Texture.TInt, Texture.FR32i)
        self.gatherGridBuffer0.setClearColor(Vec4(0))
        self.gatherGridBuffer0.clearImage()

        self.gatherGridBuffer1 = Texture("GatherGrid1")
        self.gatherGridBuffer1.setup3dTexture(self.voxelGridResolution.x, self.voxelGridResolution.y, 
                                            self.voxelGridResolution.z, Texture.TInt, Texture.FR32i)
        self.gatherGridBuffer1.setClearColor(Vec4(0))
        self.gatherGridBuffer1.clearImage()

        MemoryMonitor.addTexture("Gather Grid Buffer 0", self.gatherGridBuffer0)
        MemoryMonitor.addTexture("Gather Grid Buffer 1", self.gatherGridBuffer1)

        self.targetSpace.setShaderInput("photonBufferTex", self.photonBuffer)
        self.targetSpace.setShaderInput("photonCounterTex", self.photonCounter)

        texNoise = loader.loadTexture("Data/Textures/PhotonNoise64.png")
        texNoise.setMinfilter(SamplerState.FTNearest)
        texNoise.setMagfilter(SamplerState.FTNearest)

        photonSplitModifier = 8

        self.distributionPassSize = (self.photonBaseSize*self.photonBaseSize) / self.distributionPassCount

        self.distributionPass = RenderTarget("PhotonDistribution")
        self.distributionPass.setSize( (self.photonBaseSize / photonSplitModifier) * 4, (self.photonBaseSize / self.distributionPassCount) * photonSplitModifier * 4 )
        self.distributionPass.addColorTexture()
        self.distributionPass.prepareOffscreenBuffer()
        self.distributionPass.setActive(False)

        self.distributionPass.setShaderInput("sourcePhotonBufferTex", self.photonBuffer)
        self.distributionPass.setShaderInput("sourcePhotonCounterTex", self.photonCounter)
        self.distributionPass.setShaderInput("shiftSize", self.photonBaseSize / photonSplitModifier)
        self.distributionPass.setShaderInput("noiseTex", texNoise)

        self.distributionPass.setShaderInput("gatherGridBuffer0", self.gatherGridBuffer0)
        self.distributionPass.setShaderInput("gatherGridBuffer1", self.gatherGridBuffer1)

        self.gatherConvertBuffer = RenderTarget("GatherConvertBuffer")
        self.gatherConvertBuffer.setSize(self.voxelGridResolution.x, self.voxelGridResolution.y)
        self.gatherConvertBuffer.setColorWrite(False)
        # self.convertBuffer.addColorTexture()
        self.gatherConvertBuffer.prepareOffscreenBuffer()
        self.gatherConvertBuffer.setShaderInput("src0", self.gatherGridBuffer0)
        self.gatherConvertBuffer.setShaderInput("src1", self.gatherGridBuffer1)
        self.gatherConvertBuffer.setShaderInput("dest", self.gatherStablePongTex)
        self.gatherConvertBuffer.setActive(False)

        self.pipeline.getRenderPassManager().registerStaticVariable("photonGatherGridTex", self.gatherStableTex)

        self.bindTo(self.distributionPass, "giData")

        # Setups the render target to convert the voxel grid
        self.blurBuffer = RenderTarget("PhotonBlurBuffer")
        self.blurBuffer.setSize(self.voxelGridResolution.x, self.voxelGridResolution.y)
        self.blurBuffer.setColorWrite(False)
        # self.blurBuffer.addColorTexture()
        self.blurBuffer.prepareOffscreenBuffer()
        self.blurBuffer.setShaderInput("src", self.gatherStableTex)
        self.blurBuffer.setShaderInput("dest", self.gatherStablePongTex)
        self.blurBuffer.setShaderInput("voxelGrid", self.voxelStableTex)
        self.blurBuffer.setShaderInput("direction", Vec3(0))
        self.blurBuffer.setActive(False)


        self._updateGridPos()
        self._createDebugTexts()

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
        self._createGenerateMipmapsShader()
        self._createConvertShader()
        self._createPhotonBoxShader()
        self._createDistributionShader()
        self._createBlurShader()

        self.frameIndex = 0

    def _createPhotonBoxShader(self):
        """ Loads the shader to visualize the photons """
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultShaders/Photon/vertex.glsl",
            "Shader/DefaultShaders/Photon/fragment.glsl")
        # self.photonBox.setShader(shader, 100)

    def _updateGridPos(self):
        """ Computes the new center of the voxel grid. The center pos is also
        snapped, to avoid flickering. """

        # It is important that the grid is snapped, otherwise it will flicker 
        # while the camera moves. When using a snap of 32, everything until
        # the log2(32) = 5th mipmap is stable. 
        snap = 1.0
        stepSizeX = float(self.voxelGridSizeWS.x * 2.0) / float(self.voxelGridResolution.x) * snap
        stepSizeY = float(self.voxelGridSizeWS.y * 2.0) / float(self.voxelGridResolution.y) * snap
        stepSizeZ = float(self.voxelGridSizeWS.z * 2.0) / float(self.voxelGridResolution.z) * snap

        self.gridPos = self.targetCamera.getPos(self.targetSpace)
        self.gridPos.x -= self.gridPos.x % stepSizeX
        self.gridPos.y -= self.gridPos.y % stepSizeY
        self.gridPos.z -= self.gridPos.z % stepSizeZ

    def update(self):
        """ Processes the gi, this method is called every frame """

        # With no light, there is no gi
        if self.targetLight is None:
            self.error("The GI cannot work without a directional target light! Set one "
                "with renderPipeline.setGILightSource(directionalLight) first!")
            return

        # Fetch current light direction
        direction = self.targetLight.getDirection()

        # print "\n\nRENDER STEP"

        # Disable all render targets first
        self.convertBuffer.setActive(False)
        for child in self.mipmapTargets:
            child.setActive(False) 
        self.gatherConvertBuffer.setActive(False)
        self.voxelizePass.setActive(False)
        self.distributionPass.setActive(False)
        self.blurBuffer.setActive(False)

        if self.frameIndex == 0:

            # Set required inputs
            self.ptaLightUVStart[0] = self.helperLight.shadowSources[0].getAtlasPos()
            self.ptaLightMVP[0] = self.helperLight.shadowSources[0].mvp
            self.ptaVoxelGridStart[0] = self.gridPos - self.voxelGridSizeWS
            self.ptaVoxelGridEnd[0] = self.gridPos + self.voxelGridSizeWS
            self.ptaLightDirection[0] = direction

            # Step 1: Voxelize scene from the x-Axis
            self.photonCounter.clearImage()
            
            # Clear the old data in generation texture 
            self.voxelizePass.clearGrid()
            self.voxelizePass.voxelizeSceneFromDirection(self.gridPos, "x")


        elif self.frameIndex == 1:

            # Step 2: Voxelize scene from the y-Axis
            self.voxelizePass.voxelizeSceneFromDirection(self.gridPos, "y")

        elif self.frameIndex == 2:
            # print "voxelize z"

            # Step 3: Voxelize the scene from the z-Axis 
            self.voxelizePass.voxelizeSceneFromDirection(self.gridPos, "z")
            
        elif self.frameIndex > 2 and self.frameIndex < 3 + self.distributionPassCount:
            
            self.distributionPass.setActive(True)

            if self.frameIndex == 3:
                self.convertBuffer.setActive(True) 
                self.gatherGridBuffer0.clearImage()
                self.gatherGridBuffer1.clearImage()

                # Update helper light, so that it is at the right position when Step 1
                # starts again 
                self.helperLight.setPos(self.gridPos)
                self.helperLight.setDirection(direction)

            passIndex = self.frameIndex - 3
            # print "distribution pass nr.",passIndex
            photonOffset = passIndex * self.distributionPassSize
            self.distributionPass.setShaderInput("photonOffset", photonOffset)
            self.distributionPass.setShaderInput("baseVoxelGridPos", self.gridPos)

            if self.debugText is not None:
                self.debugText.setText("GI Pass " + str(passIndex) + " / " + str(self.distributionPassCount))

        elif self.frameIndex >= 3 + self.distributionPassCount and self.frameIndex < 6 + self.distributionPassCount:

            blurPassIdx = self.frameIndex - 3 - self.distributionPassCount

            if blurPassIdx == 0:
                # self.gatherStablePongTex.clearImage()
                # self.gatherStablePingTex.clearImage()
                self.gatherConvertBuffer.setActive(True) 

            self.blurBuffer.setActive(True)

            if blurPassIdx == 0:
                self.blurBuffer.setShaderInput("direction", Vec3(1,0,0))
                self.blurBuffer.setShaderInput("src", self.gatherStablePongTex)
                self.blurBuffer.setShaderInput("dest", self.gatherStablePingTex)

            elif blurPassIdx == 1:
                self.blurBuffer.setShaderInput("direction", Vec3(0,1,0))
                self.blurBuffer.setShaderInput("src", self.gatherStablePingTex)
                self.blurBuffer.setShaderInput("dest", self.gatherStablePongTex)

            elif blurPassIdx == 2:
                self.blurBuffer.setShaderInput("direction", Vec3(0,0,1))
                self.blurBuffer.setShaderInput("src", self.gatherStablePongTex)
                self.blurBuffer.setShaderInput("dest", self.gatherStableTex)
                self.ptaGridPos[0] = Vec3(self.gridPos)
        else:

            # Step 4: Extract voxel grid and generate mipmaps

            # for child in self.mipmapTargets:
            #     child.setActive(True)
            self._updateGridPos()
        

        # print "Targets:"
        # print "\tVoxelize Target:", self.voxelizePass.target.isActive()
        # print "\tConvert Buffer:", self.convertBuffer.isActive()
        # print "\tGather Convert Buffer:", self.gatherConvertBuffer.isActive()
        # print "\tDistribution Pass:", self.distributionPass.isActive()

        # Increase frame index
        self.frameIndex += 1
        self.frameIndex = self.frameIndex % (4 + self.distributionPassCount + 3)

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

