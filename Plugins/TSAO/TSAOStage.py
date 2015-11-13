
from .. import RenderStage

class TSAOStage(RenderStage):

    required_pipes = ["ShadedScene", "GBufferDepth", "GBuffer0", "GBuffer1", "GBuffer2"]
    required_inputs = ["mainCam", "mainRender", "currentProjMat", "cameraPosition"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, "TSAOStage", pipeline)

    def get_produced_pipes(self):
        return {"AmbientOcclusion": self._target_upscale['color']}

    def create(self):
        self._target_depth = self._create_target("TSAODownscaleView")
        self._target_depth.set_half_resolution()
        self._target_depth.add_color_texture(bits=16)
        self._target_depth.add_aux_texture(bits=16)
        self._target_depth.prepare_offscreen_buffer()
        
        self._target = self._create_target("TSAOSample")
        self._target.set_half_resolution()

        # TODO: 8 bits should be enough I think
        self._target.add_color_texture(bits=16)
        self._target.prepare_offscreen_buffer()

        self._target_upscale = self._create_target("TSAOUpscale")
        self._target_upscale.add_color_texture(bits=16)
        self._target_upscale.prepare_offscreen_buffer()

        self._target.set_shader_input("DepthSource", self._target_depth["color"])
        self._target.set_shader_input("NrmSource", self._target_depth["aux0"])
        self._target_upscale.set_shader_input("SourceTex", self._target["color"])
        
    def set_shaders(self):
        self._target_depth.set_shader(self.load_plugin_shader("DownscaleDepth.frag.glsl"))
        self._target.set_shader(self.load_plugin_shader("TSAOSample.frag.glsl"))
        self._target_upscale.set_shader(self.load_plugin_shader("TSAOUpscale.frag.glsl"))

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
