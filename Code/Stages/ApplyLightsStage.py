
from ..RenderStage import RenderStage


class ApplyLightsStage(RenderStage):

    """ This stage applies the lights to the scene using the gbuffer """

    required_pipes = ["GBuffer", "CellIndices", "PerCellLights"]
    required_inputs = ["AllLightsData", "mainCam", "mainRender", "cameraPosition", "IESDatasetTex"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, "ApplyLightsStage", pipeline)

    def get_produced_pipes(self):
        return {"ShadedScene": self._target['color']}

    def create(self):
        self._target = self._create_target("ApplyLights")
        self._target.add_color_texture(bits=16)
        self._target.prepare_offscreen_buffer()

    def set_shaders(self):
        self._target.set_shader(self._load_shader("Stages/ApplyLights.frag"))

    def resize(self):
        self.debug("Resizing pass")

    def cleanup(self):
        self.debug("Cleanup pass")
