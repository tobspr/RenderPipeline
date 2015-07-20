
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, GeomEnums

from ..Globals import Globals
from ..RenderPass import RenderPass
from ..RenderTarget import RenderTarget

class CloudRenderPass(RenderPass):

    """ This pass renders the clouds from the cloud grid """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "CloudRenderPass"

    def getRequiredInputs(self):
        return {
            "mainRender": "Variables.mainRender",
            "mainCam": "Variables.mainCam",
            "worldSpaceNormals": "DeferredScenePass.wsNormal",
            "worldSpacePosition": "DeferredScenePass.wsPosition",
            "cameraPosition": "Variables.cameraPosition",

            "cloudVoxelGrid": "Variables.cloudVoxelGrid",
            "cloudNoise": "Variables.cloudNoise",
            "cloudStartHeight": "Variables.cloudStartHeight",
            "cloudEndHeight": "Variables.cloudEndHeight",

            "scatteringOptions": ["Variables.scatteringOptions", "Variables.null"],
            "fallbackCubemap": "Variables.defaultEnvironmentCubemap",

        }

    def create(self):
        self.target = RenderTarget("Cloud Rendering")
        self.target.setHalfResolution()
        self.target.setColorBits(16)
        self.target.setAuxBits(16)
        self.target.addColorTexture()
        self.target.addAuxTexture()
        self.target.prepareOffscreenBuffer()

        self.targetV = RenderTarget("CloudBlurV")
        self.targetV.addColorTexture()
        self.targetV.setColorBits(16)
        self.targetV.prepareOffscreenBuffer()
 
        self.targetH = RenderTarget("CloudBlurH")
        self.targetH.addColorTexture()
        self.targetH.setColorBits(16)
        self.targetH.prepareOffscreenBuffer()

        self.targetV.setShaderInput("previousTex", self.target.getColorTexture())
        self.targetH.setShaderInput("previousTex", self.targetV.getColorTexture())
        self.targetV.setShaderInput("cloudPos", self.target.getAuxTexture(0))
        self.targetH.setShaderInput("cloudPos", self.target.getAuxTexture(0))
 
    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/RenderClouds.fragment")
        self.target.setShader(shader)

        shaderV = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/CloudBlurV.fragment")
        self.targetV.setShader(shaderV)

        shaderH = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/CloudBlurH.fragment")
        self.targetH.setShader(shaderH)

        return [shader]

    def getOutputs(self):
        return {
            "CloudRenderPass.resultTex": lambda: self.targetH.getColorTexture(),
        }
