
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums, Vec3
from panda3d.core import Camera, OrthographicLens, CullFaceAttrib, DepthTestAttrib
from panda3d.core import SamplerState, Vec4, BitMask32

from ..Globals import Globals
from ..RenderPass import RenderPass
from ..RenderTarget import RenderTarget
from ..MemoryMonitor import MemoryMonitor

class VoxelizePass(RenderPass):

    """ This pass manages voxelizing the scene from multiple directions to generate
    a 3D voxel grid. It handles the camera setup and provides a simple interface. """

    def __init__(self, pipeline):
        RenderPass.__init__(self)
        self.pipeline = pipeline

    def getID(self):
        return "VoxelizePass"

    def getRequiredInputs(self):
        return {

            # Lighting
            "renderedLightsBuffer": "Variables.renderedLightsBuffer",
            "lights": "Variables.allLights",
            "shadowAtlasPCF": "ShadowScenePass.atlasPCF",
            "shadowAtlas": "ShadowScenePass.atlas",
            "shadowSources": "Variables.allShadowSources",
            "directionToFace": "Variables.directionToFaceLookup",

            "cameraPosition": "Variables.cameraPosition",
            "mainCam": "Variables.mainCam",
            "mainRender": "Variables.mainRender",

        }

    def setVoxelGridResolution(self, voxelGridResolution):
        """ Sets the voxel grid resolution, this is the amount of voxels in every
        direction, so the voxel grid will have voxelGridResolution**3 total voxels. """
        self.voxelGridResolution = voxelGridResolution

    def setVoxelGridSize(self, voxelGridSize):
        """ Sets the size of the voxel grid in world space units. This is the
        size going from the mid of the voxel grid, so the effective voxel grid
        will have twice the size specified in voxelGridSize """
        self.voxelGridSize = voxelGridSize

    def setGridResolutionMultiplier(self, factor):
        """ Sets the density of the voxel grid. """
        self.gridResolutionMultiplier = factor

    def setActive(self, active):
        """ Enables and disables this pass """
        if hasattr(self, "target"):
            self.target.setActive(active)

    def getVoxelTex(self):
        """ Returns a handle to the generated voxel texture """
        return self.voxelGenTex

    def clearGrid(self):
        """ Clears the voxel grid """
        self.voxelGenTex.clearImage()

    def create(self):
        # Create voxelize camera
        self.voxelizeCamera = Camera("VoxelizeScene")
        self.voxelizeCamera.setCameraMask(BitMask32.bit(4))
        self.voxelizeCameraNode = Globals.render.attachNewNode(self.voxelizeCamera)
        self.voxelizeLens = OrthographicLens()
        self.voxelizeLens.setFilmSize(self.voxelGridSize*2, self.voxelGridSize*2)
        self.voxelizeLens.setNearFar(0.0, self.voxelGridSize*2)
        self.voxelizeCamera.setLens(self.voxelizeLens)
        self.voxelizeCamera.setTagStateKey("VoxelizePassShader")
        Globals.render.setTag("VoxelizePassShader", "Default")

        # Create voxelize tareet
        self.target = RenderTarget("VoxelizePass")
        self.target.setSize(self.voxelGridResolution * self.gridResolutionMultiplier)
        
        if self.pipeline.settings.useDebugAttachments:
            self.target.addColorTexture()
        else:
            self.target.setColorWrite(False)

        self.target.setCreateOverlayQuad(False)
        self.target.setSource(self.voxelizeCameraNode, Globals.base.win)
        self.target.prepareSceneRender()
        self.target.setActive(False)

        # self.target.getInternalRegion().setSort(-400)
        # self.target.getInternalBuffer().setSort(-399)

    def voxelizeSceneFromDirection(self, gridPos, direction="x"):
        """ Voxelizes the scene from a given direction. This method handles setting 
        the camera position aswell as the near and far plane. If the pass was disabled,
        it also enables this pass.  """
        assert(direction in ["x", "y","z"])
        self.setActive(True)

        if direction == "x":
            self.voxelizeLens.setFilmSize(self.voxelGridSize*2, self.voxelGridSize * 2)
            self.voxelizeLens.setNearFar(0.0, self.voxelGridSize*2)
            self.voxelizeCameraNode.setPos(gridPos - Vec3(self.voxelGridSize, 0, 0))
            self.voxelizeCameraNode.lookAt(gridPos)
        elif direction == "y":
            self.voxelizeLens.setFilmSize(self.voxelGridSize*2, self.voxelGridSize*2)
            self.voxelizeLens.setNearFar(0.0, self.voxelGridSize*2)
            self.voxelizeCameraNode.setPos(gridPos - Vec3(0, self.voxelGridSize, 0))
            self.voxelizeCameraNode.lookAt(gridPos)
        elif direction == "z":
            self.voxelizeLens.setFilmSize(self.voxelGridSize*2, self.voxelGridSize*2)
            self.voxelizeLens.setNearFar(0.0, self.voxelGridSize*2)
            self.voxelizeCameraNode.setPos(gridPos + Vec3(0, 0, self.voxelGridSize))
            self.voxelizeCameraNode.lookAt(gridPos)

    def setShaders(self):
        """ Creates the tag state and loades the voxelizer shader """
        self.registerTagState("Default", NodePath("DefaultVoxelizeState"))
        return []

    def registerTagState(self, name, state):
        """ Registers a new tag state """
        state.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullNone))
        state.setDepthWrite(False)
        state.setDepthTest(False)
        state.setAttrib(DepthTestAttrib.make(DepthTestAttrib.MNone))
        state.setShaderInput("voxelizeCam", self.voxelizeCameraNode)
        self.voxelizeCamera.setTagState(name, state.getState()) 

    def setShaderInput(self, *args):
        Globals.base.render.setShaderInput(*args)

    def getOutputs(self):
        return {
        }


