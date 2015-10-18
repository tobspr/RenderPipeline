


from .. import *

class ScatteringStage(RenderStage):

    """ This stage uses the precomputed data to display the scattering """

    def __init__(self, pipeline):
        RenderStage.__init__(self, "ScatteringStage", pipeline)

    def get_produced_pipes(self):
        return {
            "ShadedScene": self._target['color']
        }

    def get_input_pipes(self):
        return ["ShadedScene", "GBufferDepth", "GBuffer0", "GBuffer1",
                "GBuffer2"]

    def get_required_inputs(self):
        return ["mainCam", "mainRender", "cameraPosition"]

    def create(self):
        self._target = self._create_target("ScatteringStage")
        self._target.add_color_texture()
        self._target.set_color_bits(16)
        self._target.prepare_offscreen_buffer()

    def set_shaders(self):
        self._target.set_shader(
            self._load_plugin_shader("Scattering", "ApplyScattering.frag.glsl"))

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
