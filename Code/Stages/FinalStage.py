
from ..RenderStage import RenderStage


class FinalStage(RenderStage):

    """ This stage is the final stage and outputs the shaded scene to the
    screen """

    required_pipes = ["ShadedScene"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, "FinalStage", pipeline)

    def create(self):
        self._target = self._create_target("FinalStage")

        # We don't have a color attachment, but still want to write color
        self._target.set_color_write(True)
        self._target.prepare_offscreen_buffer()
        self._target.make_main_target()


    def set_shaders(self):
        self._target.set_shader(self._load_shader("Stages/FinalStage.frag"))

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
