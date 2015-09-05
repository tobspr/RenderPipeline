
import math

from panda3d.core import Texture, Shader, Vec4

from ..RenderStage import RenderStage
from ..Util.RenderTarget import RenderTarget
from ..Util.Image import Image

class CullLightsStage(RenderStage):

    def __init__(self, pipeline):
        RenderStage.__init__(self, "CullLightsStage", pipeline)
        self.tileAmount = None

    def setTileAmount(self, tileAmount):
        """ Sets the cell tile size """
        self.tileAmount = tileAmount

    def getInputPipes(self):
        return ["CellListBuffer"]

    def getProducedPipes(self):
        return {
            "PerCellLights": self.perCellLights.tex
        }

    def getProducedDefines(self):
        return {
            "LC_SHADE_SLICES": self.numRows
        }

    def create(self):
        maxCells = self.tileAmount.x * self.tileAmount.y * self.pipeline.settings.lightGridSlices
        self.numRows = int(math.ceil(maxCells / 512.0))

        self.target = self._createTarget("CullLights")
        self.target.setSize(512, self.numRows)
        self.target.addColorTexture()
        self.target.prepareOffscreenBuffer()
        self.target.setClearColor(color=Vec4(0.2, 0.6, 1.0, 1.0))

        self.perCellLights = Image.createBuffer("PerCellLights", maxCells, Texture.TInt, Texture.FR16)
        self.perCellLights.setClearColor(0)

        self.target.setShaderInput("perCellLightsBuffer", self.perCellLights.tex)

    def update(self):
        # self.cellListBuffer.clearImage()
        # self.cellIndexBuffer.clearImage()
        pass

    def setShaders(self):
        self.target.setShader(self._loadShader("Stages/CullLights.vertex", "Stages/CullLights.fragment"))

    def resize(self):
        self.debug("Resizing pass")

    def cleanup(self):
        self.debug("Cleanup pass")
    


