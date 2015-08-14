
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums

from ..Globals import Globals
from ..RenderPass import RenderPass
from ..RenderTarget import RenderTarget
from ..MemoryMonitor import MemoryMonitor

class GlobalIlluminationPass(RenderPass):

    """ This pass performs voxel cone tracing over the previously generated
    voxel grid to compute a diffuse, specular and ambient term which can be
    used later in the lighting pass """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "GlobalIlluminationPass"

    def getRequiredInputs(self):
        return {

            "normalTex": "DeferredScenePass.wsNormal",
            "depthTex": "DeferredScenePass.depth",
            "skyboxMask": "SkyboxMaskPass.resultTex",

            "giData": "Variables.giData",
            "giReadyState": "Variables.giReadyState",

            "giVoxelData0": "Variables.giVoxelData0",
            "giVoxelData1": "Variables.giVoxelData1",
            "giVoxelData2": "Variables.giVoxelData2",
            "giVoxelData3": "Variables.giVoxelData3",
            "giVoxelData4": "Variables.giVoxelData4",
           
            "cameraPosition": "Variables.cameraPosition",
            "mainCam": "Variables.mainCam",
            "mainRender": "Variables.mainRender"
        }

    def create(self):
        self.target = RenderTarget("GlobalIlluminationPass")
        # self.target.setHalfResolution()
        self.target.addColorTexture()
        self.target.addAuxTexture()
        self.target.setColorBits(16)
        # self.target.setAuxBits(16)
        self.target.prepareOffscreenBuffer()
 
    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/ComputeGI.fragment")
        self.target.setShader(shader)
        
        return [shader]

    def getOutputs(self):
        return {
            "GlobalIlluminationPass.diffuseResult": lambda: self.target.getColorTexture(),
            "GlobalIlluminationPass.specularResult": lambda: self.target.getAuxTexture(0)
        }


