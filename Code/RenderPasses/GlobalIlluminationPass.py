
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums

from Code.Globals import Globals
from Code.RenderPass import RenderPass
from Code.RenderTarget import RenderTarget
from Code.LightLimits import LightLimits
from Code.MemoryMonitor import MemoryMonitor

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

            "data0": "DeferredScenePass.data0",
            "data1": "DeferredScenePass.data1",
            "data2": "DeferredScenePass.data2",
            "data3": "DeferredScenePass.data3",
            "giData": "Variables.giVoxelGridData",
            "photonGatherGridTex": "Variables.photonGatherGridTex",
            

            "cameraPosition": "Variables.cameraPosition",
            "mainCam": "Variables.mainCam",
            "mainRender": "Variables.mainRender"
        }

    def create(self):
        self.target = RenderTarget("GlobalIlluminationPass")
        self.target.setHalfResolution()
        self.target.addColorTexture()
        self.target.addAuxTexture()
        self.target.setColorBits(16)
        self.target.setAuxBits(16)
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


