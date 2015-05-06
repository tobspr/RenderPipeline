
from panda3d.core import NodePath, Shader, LVecBase2i, Texture, PTAFloat, Vec4

from Code.Globals import Globals
from Code.RenderPass import RenderPass
from Code.RenderTarget import RenderTarget

class FinalPostprocessPass(RenderPass):

    def __init__(self):
        RenderPass.__init__(self)


    def getID(self):
        return "FinalPostprocessPass"

    def getRequiredInputs(self):
        return {
            "colorTex": "LightingPass.resultTex",
        }

    def create(self):
        self.target = RenderTarget("Final Pass")
        self.target.addColorTexture()

        # self.target.setSource(Globals.base.cam, Globals.base.win, Globals.base.win.getDisplayRegion(0))

        self.target.prepareOffscreenBuffer()
        Globals.base.win.getDisplayRegion(1).setCamera(self.target._quad.getChild(0))

        
        # Globals.base.win.getDisplayRegion(2).setSort(1000)

        # for dr in Globals.base.win.getActiveDisplayRegions():
            # print dr

        # self.target.getInternalBuffer().setSort(2000)
        # self.target.getInternalBuffer().getDisplayRegion(0).setSort(2000)
        # self.target.getInternalRegion().setSort(2000)

    def setShaders(self):
        shader = Shader.load(Shader.SLGLSL, 
            "Shader/DefaultPostProcess.vertex",
            "Shader/Final.fragment")
        self.target.setShader(shader)

    def getOutputs(self):
        return {
        }
