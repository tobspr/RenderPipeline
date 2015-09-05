
from panda3d.core import Texture, Shader

from ..RenderStage import RenderStage
from ..Util.RenderTarget import RenderTarget
from ..Util.Image import Image

class FlagUsedCellsStage(RenderStage):

    def __init__(self, pipeline):
        RenderStage.__init__(self, "FlagUsedCellsStage", pipeline)
        self.tileAmount = None

    def setTileAmount(self, tileAmount):
        """ Sets the cell tile size """
        self.tileAmount = tileAmount

    def getInputPipes(self):
        return ["GBufferDepth"]

    def getProducedPipes(self):
        return {"FlaggedCells": self.cellGridFlags.tex}

    def create(self):

        self.target = self._createTarget("FlagUsedCells")
        self.target.addColorTexture()
        self.target.prepareOffscreenBuffer()

        self.cellGridFlags = Image.create2DArray("CellGridFlags", self.tileAmount.x, 
            self.tileAmount.y, self.pipeline.settings.lightGridSlices, Texture.TFloat, Texture.FR16)
        self.cellGridFlags.setClearColor(0)

        self.target.setShaderInput("cellGridFlags", self.cellGridFlags.tex)

    def update(self):
        self.cellGridFlags.clearImage()

    def setShaders(self):
        self.target.setShader(self._loadShader("Stages/FlagUsedCells.fragment"))

    def resize(self):
        self.debug("Resizing pass")

    def cleanup(self):
        self.debug("Cleanup pass")
    


