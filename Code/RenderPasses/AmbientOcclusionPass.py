
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums

from ..Globals import Globals
from ..RenderPass import RenderPass
from ..RenderTarget import RenderTarget

class AmbientOcclusionPass(RenderPass):

    """ This pass computes the screen space ambient occlusion if enabled in the
     settings. As many samples are required for a good looking result, the pass
     is done at half resolution and then upscaled by the edge preserving blur
     pass """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "AmbientOcclusionPass"

    def getRequiredInputs(self):
        return {
            "frameIndex": "Variables.frameIndex",
            "mainRender": "Variables.mainRender",
            "mainCam": "Variables.mainCam",
            "noiseTexture": "Variables.noise4x4",
            "viewSpaceNormals": "ViewSpacePass.normals",
            "viewSpacePosition": "ViewSpacePass.position",
            "worldSpaceNormals": "DeferredScenePass.wsNormal",
            "worldSpacePosition": "DeferredScenePass.wsPosition",
            "depthTex": "DeferredScenePass.depth",
            "cameraPosition": "Variables.cameraPosition",
        }

    def create(self):
        self.target = RenderTarget("AmbientOcclusion")
        self.target.setHalfResolution()
        self.target.addColorTexture()
        self.target.prepareOffscreenBuffer()
 
    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/ComputeOcclusion.fragment")
        self.target.setShader(shader)
        return [shader]

    def getOutputs(self):
        return {
            "AmbientOcclusionPass.computeResult": lambda: self.target.getColorTexture(),
        }
