
import math

from panda3d.core import Texture, Vec4

from ..RenderStage import RenderStage
from ..Util.Image import Image


class CullLightsStage(RenderStage):

    """ This stage takes the list of used cells and creates a list of lights
    for each cell """

    def __init__(self, pipeline):
        RenderStage.__init__(self, "CullLightsStage", pipeline)
        self._tile_amount = None
        self._max_lights_per_cell = 512

    def set_tile_amount(self, tile_amount):
        """ Sets the cell tile size """
        self._tile_amount = tile_amount

    def get_input_pipes(self):
        return ["CellListBuffer"]

    def get_produced_pipes(self):
        return {
            "PerCellLights": self._per_cell_lights.tex
        }

    def get_produced_defines(self):
        return {
            "LC_SHADE_SLICES": self._num_rows,
            "MAX_LIGHTS_PER_CELL": self._max_lights_per_cell
        }

    def get_required_inputs(self):
        return ["AllLightsData", "maxLightIndex", "mainCam", "currentViewMat"]

    def create(self):
        max_cells = self._tile_amount.x * self._tile_amount.y * \
            self._pipeline.settings.lightGridSlices

        self._num_rows = int(math.ceil(max_cells / 512.0))
        self._target = self._create_target("CullLights")
        self._target.setSize(512, self._num_rows)
        # self._target.addColorTexture()
        self._target.prepareOffscreenBuffer()
        self._target.setClearColor(color=Vec4(0.2, 0.6, 1.0, 1.0))

        self._per_cell_lights = Image.create_buffer("PerCellLights",
            max_cells * (self._max_lights_per_cell + 1), Texture.T_int,
            Texture.F_r32)
        self._per_cell_lights.set_clear_color(0)

        self._target.setShaderInput("perCellLightsBuffer",
            self._per_cell_lights.tex)

    def update(self):
        # self.perCellLights.clearImage()
        pass

    def set_shaders(self):
        self._target.setShader(self._load_shader("Stages/CullLights.vertex",
                                                "Stages/CullLights.fragment"))

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
