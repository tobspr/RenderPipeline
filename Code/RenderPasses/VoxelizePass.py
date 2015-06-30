
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums, Vec3
from panda3d.core import Camera, OrthographicLens, CullFaceAttrib, DepthTestAttrib
from panda3d.core import SamplerState, Vec4, BitMask32

from Code.Globals import Globals
from Code.RenderPass import RenderPass
from Code.RenderTarget import RenderTarget
from Code.MemoryMonitor import MemoryMonitor

class VoxelizePass(RenderPass):

    """ This pass manages voxelizing the scene from multiple directions to generate
    a 3D voxel grid. It handles the camera setup and provides a simple interface. """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "VoxelizePass"

    def getRequiredInputs(self):
        return {
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

    def setPhotonScaleFactor(self, factor):
        """ Sets the density of the photon grid. A number of 1 means that for
        every bright voxel 1 photon will be spawned. A number of 4 for example
        means that for ever bright voxel 4x4x4 = 64 Photons will be spawned. """
        self.photonScaleFactor = factor

    def setActive(self, active):
        """ Enables and disables this pass """
        self.target.setActive(active)

    def initVoxelStorage(self):
        """ Creates t he 3D Texture to store the voxel generation grid """
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

        # Register texture
        MemoryMonitor.addTexture("Voxel Temp Texture", self.voxelGenTex)

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
        self.voxelizeLens.setFilmSize(self.voxelGridSize.x*2, self.voxelGridSize.y*2)
        self.voxelizeLens.setNearFar(0.0, self.voxelGridSize.x*2)
        self.voxelizeCamera.setLens(self.voxelizeLens)
        self.voxelizeCamera.setTagStateKey("VoxelizePassShader")
        Globals.render.setTag("VoxelizePassShader", "Default")

        # Create voxelize tareet
        self.target = RenderTarget("VoxelizePass")
        self.target.setSize(self.voxelGridResolution.x * self.photonScaleFactor)
        # self.target.setColorWrite(False)
        self.target.addColorTexture()
        self.target.setCreateOverlayQuad(False)
        self.target.setSource(self.voxelizeCameraNode, Globals.base.win)
        self.target.prepareSceneRender()
        self.target.setActive(False)

        self.target.getInternalRegion().setSort(-400)
        self.target.getInternalBuffer().setSort(-399)

    def voxelizeSceneFromDirection(self, gridPos, direction="x"):
        """ Voxelizes the scene from a given direction. This method handles setting 
        the camera position aswell as the near and far plane. If the pass was disabled,
        it also enables this pass.  """
        assert(direction in "x y z".split())
        self.setActive(True)

        if direction == "x":
            self.voxelizeLens.setFilmSize(self.voxelGridSize.y*2, self.voxelGridSize.z*2)
            self.voxelizeLens.setNearFar(0.0, self.voxelGridSize.x*2)
            self.voxelizeCameraNode.setPos(gridPos - Vec3(self.voxelGridSize.x, 0, 0))
            self.voxelizeCameraNode.lookAt(gridPos)
        elif direction == "y":
            self.voxelizeLens.setFilmSize(self.voxelGridSize.x*2, self.voxelGridSize.z*2)
            self.voxelizeLens.setNearFar(0.0, self.voxelGridSize.y*2)
            self.voxelizeCameraNode.setPos(gridPos - Vec3(0, self.voxelGridSize.y, 0))
            self.voxelizeCameraNode.lookAt(gridPos)
        elif direction == "z":
            self.voxelizeLens.setFilmSize(self.voxelGridSize.x*2, self.voxelGridSize.y*2)
            self.voxelizeLens.setNearFar(0.0, self.voxelGridSize.z*2)
            self.voxelizeCameraNode.setPos(gridPos + Vec3(0, 0, self.voxelGridSize.z))
            self.voxelizeCameraNode.lookAt(gridPos)

    def setShaders(self):
        """ Creates the tag state and loades the voxelizer shader """
        voxelizeShader = Shader.load(Shader.SLGLSL, 
            "Shader/GI/Voxelize.vertex",
            "Shader/GI/Voxelize.fragment")

        # Create tag state
        initialState = NodePath("VoxelizerState")
        initialState.setShader(voxelizeShader, 500)
        initialState.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullNone))
        initialState.setDepthWrite(False)
        initialState.setDepthTest(False)
        initialState.setAttrib(DepthTestAttrib.make(DepthTestAttrib.MNone))
        initialState.setShaderInput("giVoxelGenerationTex", self.voxelGenTex)

        # Apply tag state
        self.voxelizeCamera.setTagState("Default", initialState.getState())

        return [voxelizeShader]

    def getOutputs(self):
        return {
        }
