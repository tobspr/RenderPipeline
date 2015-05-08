
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, PTAFloat, Vec4

from Code.Globals import Globals
from Code.RenderPass import RenderPass
from Code.RenderTarget import RenderTarget

class FinalPostprocessPass(RenderPass):

    """ This pass does the final postprocessing, including color correction and
    adding a vignette. """

    def __init__(self):
        RenderPass.__init__(self)

    def getID(self):
        return "FinalPostprocessPass"

    def getRequiredInputs(self):
        return {
            "colorTex": ["AntialiasingPass.resultTex", "LightingPass.resultTex"],
            "colorLUT": "Variables.colorLUT"
        }

    def create(self):
        self.target = RenderTarget("Final Pass")
        self.target.addColorTexture()
        self.target.prepareOffscreenBuffer()

        # Make this pass show on the screen
        Globals.base.win.getDisplayRegion(1).setCamera(self.target._quad.getChild(0))

    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/Final.fragment")
        self.target.setShader(shader)
