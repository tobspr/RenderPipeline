
from panda3d.core import NodePath, Shader, Texture, CardMaker, TransparencyAttrib
from panda3d.core import ColorBlendAttrib, Vec4, OmniBoundingVolume

from ..Globals import Globals
from ..RenderPass import RenderPass
from ..RenderTarget import RenderTarget

class ApplyLightsPass(RenderPass):

    """ This pass applies the lights """

    def __init__(self, pipeline):
        RenderPass.__init__(self)
        self.pipeline = pipeline
        self.tileCount = None

    def getID(self):
        return "ApplyLightsPass"

    def setTileCount(self, tileCount):
        self.tileCount = tileCount

    def getRequiredInputs(self):
        return {
            "depthTex": "DeferredScenePass.depth"
        }

    def create(self):
        self.target = RenderTarget("ApplyLights")
        self.target.addColorTexture()
        self.target.setColorBits(16)
        self.target.prepareOffscreenBuffer()
        self.target.setClearColor(True)

        self.target.getQuad().removeNode()
        self.target.getNode().setAttrib(TransparencyAttrib.make(TransparencyAttrib.MNone), 1000)
        self.target.getNode().setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd), 1000)

        self.quads = {}

        numInstances = self.tileCount.x * self.tileCount.y

        for lightType in ["DirectionalLightShadow"]:
            cm = CardMaker("BufferQuad-" + lightType)
            cm.setFrameFullscreenQuad()
            quad = NodePath(cm.generate())
            quad.setDepthTest(0)
            quad.setDepthWrite(0)
            quad.setAttrib(TransparencyAttrib.make(TransparencyAttrib.MNone), 1000)
            quad.setColor(Vec4(1, 0.5, 0.5, 1))

            # Disable culling
            quad.node().setFinal(True)
            quad.node().setBounds(OmniBoundingVolume())
            quad.setBin("unsorted", 10)
            quad.setInstanceCount(numInstances)

            quad.reparentTo(self.target.getNode())

            self.quads[lightType] = quad

        self.target.getNode().setShaderInput("tileCount", self.tileCount)
 
    def setShaders(self):
        for name, quad in self.quads.iteritems():
            shader = Shader.load(Shader.SLGLSL, 
                "Shader/ApplyLights/ApplyLights.vertex",
                "Shader/ApplyLights/" + name + ".fragment",
                "Shader/ApplyLights/ApplyLights.geometry")
            quad.setShader(shader)

        return []

    def setShaderInput(self, *args):
        self.target._node.setShaderInput(*args)

    def getOutputs(self):
        return {
            "SkyboxMaskPass.resultTex": lambda: self.target.getColorTexture(),
        }
