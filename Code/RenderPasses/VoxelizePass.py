
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums, Vec3
from panda3d.core import Camera, OrthographicLens, CullFaceAttrib, DepthTestAttrib
from panda3d.core import SamplerState, Vec4

from Code.Globals import Globals
from Code.RenderPass import RenderPass
from Code.RenderTarget import RenderTarget
from Code.MemoryMonitor import MemoryMonitor

class VoxelizePass(RenderPass):

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "VoxelizePass"

    def getRequiredInputs(self):
        return {
        }

    def setVoxelGridResolution(self, voxelGridResolution):
        self.voxelGridResolution = voxelGridResolution

    def setVoxelGridSize(self, voxelGridSize):
        self.voxelGridSize = voxelGridSize

    def setActive(self, active):
        self.target.setActive(active)

    def initVoxelStorage(self):
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


    def getVoxelTex(self):
        return self.voxelGenTex

    def clearGrid(self):
        self.voxelGenTex.clearImage()

    def create(self):
        # Register texture
        MemoryMonitor.addTexture("Voxel Temp Texture", self.voxelGenTex)

        # Create voxelize camera
        self.voxelizeCamera = Camera("VoxelizeScene")
        self.voxelizeCameraNode = Globals.render.attachNewNode(self.voxelizeCamera)
        self.voxelizeLens = OrthographicLens()
        self.voxelizeLens.setFilmSize(self.voxelGridSize.x*2, self.voxelGridSize.y*2)
        self.voxelizeLens.setNearFar(0.0, self.voxelGridSize.x*2)
        self.voxelizeCamera.setLens(self.voxelizeLens)
        self.voxelizeCamera.setTagStateKey("VoxelizePassShader")
        Globals.render.setTag("VoxelizePassShader", "Default")

        # Create voxelize tareet
        self.target = RenderTarget("VoxelizePass")
        self.target.setSize( self.voxelGridResolution.x * 4 )
        # self.target.setColorWrite(False)
        self.target.addColorTexture()
        self.target.setSource(self.voxelizeCameraNode, Globals.base.win)
        self.target.prepareSceneRender()

        self.target.getQuad().node().removeAllChildren()
        self.target.getInternalRegion().setSort(-400)
        self.target.getInternalBuffer().setSort(-399)

    def voxelizeSceneFromDirection(self, gridPos, direction="x"):
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


    def _createVoxelizeState(self):
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

    def setShaders(self):
        self._createVoxelizeState()

    def getOutputs(self):
        return {
            "VoxelizePass.voxelizedScene": lambda: self.targetH.getColorTexture(),
        }

    def setShaderInput(self, name, value):
        self.targetH.setShaderInput(name, value)
        self.targetV.setShaderInput(name, value)
