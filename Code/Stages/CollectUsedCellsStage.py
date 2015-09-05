
from panda3d.core import Texture, Shader

from ..RenderStage import RenderStage
from ..Util.RenderTarget import RenderTarget
from ..Util.Image import Image

class CollectUsedCellsStage(RenderStage):

    def __init__(self, pipeline):
        RenderStage.__init__(self, "CollectUsedCellsStage", pipeline)
        self.tileAmount = None

    def setTileAmount(self, tileAmount):
        """ Sets the cell tile size """
        self.tileAmount = tileAmount

    def getInputPipes(self):
        return ["FlaggedCells"]

    def getProducedPipes(self):
        return {
            "CellListBuffer": self.cellListBuffer.tex,
            "CellIndices": self.cellIndexBuffer.tex,
        }

    def create(self):

        self.clearBufferTarget = self._createTarget("ClearCellBuffer")
        self.clearBufferTarget.setSize(1, 1)
        self.clearBufferTarget.addColorTexture()
        self.clearBufferTarget.prepareOffscreenBuffer()

        self.target = self._createTarget("CollectUsedCells")
        self.target.setSize(self.tileAmount.x, self.tileAmount.y)
        self.target.addColorTexture()
        self.target.prepareOffscreenBuffer()

        maxCells = self.tileAmount.x * self.tileAmount.y * self.pipeline.settings.lightGridSlices
        self.debug("Allocating", maxCells,"cells")

        self.cellListBuffer = Image.createBuffer("CellList", maxCells, Texture.TInt, Texture.FR32i)
        self.cellListBuffer.setClearColor(0)

        self.cellIndexBuffer = Image.create2DArray("CellIndices", self.tileAmount.x, 
            self.tileAmount.y, self.pipeline.settings.lightGridSlices, Texture.TInt, Texture.FR32i)
        self.cellIndexBuffer.setClearColor(0)

        self.target.setShaderInput("cellListBuffer", self.cellListBuffer.tex)
        self.target.setShaderInput("cellListIndices", self.cellIndexBuffer.tex)

        self.clearBufferTarget.setShaderInput("target", self.cellListBuffer.tex)

    def update(self):
        # self.cellListBuffer.clearImage()
        self.cellIndexBuffer.clearImage()

    def setShaders(self):
        self.target.setShader(self._loadShader("Stages/CollectUsedCells.fragment"))
        self.clearBufferTarget.setShader(self._loadShader("Stages/ClearCellBuffer.fragment"))

    def resize(self):
        self.debug("Resizing pass")

    def cleanup(self):
        self.debug("Cleanup pass")
    


