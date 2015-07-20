
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums

from ..Globals import Globals
from ..RenderPass import RenderPass
from ..RenderTarget import RenderTarget

class ScatteringPass(RenderPass):

    """ This pass computes the scattering if specified in the settings """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "ScatteringPass"

    def getRequiredInputs(self):
        return {

            # Scattering
            "transmittanceSampler": ["Variables.transmittanceSampler", "Variables.emptyTextureWhite"],
            "inscatterSampler": ["Variables.inscatterSampler", "Variables.emptyTextureWhite"],
            "scatteringOptions": ["Variables.scatteringOptions", "Variables.null"],

            "mainRender": "Variables.mainRender",
            "cameraPosition": "Variables.cameraPosition",
            "mainCam": "Variables.mainCam",

            "wsPositionTex": "DeferredScenePass.wsPosition",
            "basecolorTex": "DeferredScenePass.data3",
            # "viewSpaceNormals": "ViewSpacePass.normals",
            # "viewSpacePosition": "ViewSpacePass.position"

            "cloudsTex": ["CloudRenderPass.resultTex", "Variables.emptyTextureWhite"]
        }

    def create(self):
        self.target = RenderTarget("Scattering")
        self.target.addColorTexture()
        self.target.setColorBits(16)
        self.target.prepareOffscreenBuffer()
 
    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/ScatteringPass.fragment")
        self.target.setShader(shader)
        return [shader]

    def getOutputs(self):
        return {
            "ScatteringPass.resultTex": lambda: self.target.getColorTexture(),
        }
