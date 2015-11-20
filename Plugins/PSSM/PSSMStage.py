
from .. import *

class PSSMStage(RenderStage):

    """ This stage uses the PSSM Shadow map to render the shadows """

    required_inputs = ["mainCam", "mainRender", "cameraPosition", "TimeOfDay"]
    required_pipes = ["ShadedScene", "PSSMShadowAtlas", "GBufferDepth", 
                      "GBuffer0", "GBuffer1", "GBuffer2", "PSSMShadowAtlasPCF"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, "PSSMStage", pipeline)

    def get_produced_pipes(self):
        return {"ShadedScene": self._target['color']}

    def create(self):
        self._target = self._create_target("PSSMStage")
        self._target.add_color_texture(bits=16)
        self._target.prepare_offscreen_buffer()

    def set_shaders(self):
        self._target.set_shader(self.load_plugin_shader("ApplyPSSMShadows.frag.glsl"))

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
