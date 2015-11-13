
from .. import RenderStage

class AOStage(RenderStage):

    required_pipes = ["ShadedScene", "GBufferDepth", "GBuffer0", "GBuffer1", "GBuffer2"]
    required_inputs = ["mainCam", "mainRender", "currentProjMat", "cameraPosition"]

    def __init__(self, pipeline):
        RenderStage.__init__(self, "AOStage", pipeline)

    def get_produced_pipes(self):
        return {"AmbientOcclusion": self._target_upscale['color']}

    def create(self):
        self._target_depth = self._create_target("AODownscaleView")
        self._target_depth.add_color_texture(bits=32)
        self._target_depth.add_aux_texture(bits=16)
        self._target_depth.prepare_offscreen_buffer()
        
        self._target = self._create_target("AOSample")
        self._target.set_half_resolution()

        # TODO: 8 bits should be enough I think
        self._target.add_color_texture(bits=16)
        self._target.prepare_offscreen_buffer()

        self._target_upscale = self._create_target("AOUpscale")
        self._target_upscale.add_color_texture(bits=16)
        self._target_upscale.prepare_offscreen_buffer()

        self._target.set_shader_input("ViewSpacePosDepth", self._target_depth["color"])
        self._target.set_shader_input("ViewSpaceNormals", self._target_depth["aux0"])
        self._target_upscale.set_shader_input("SourceTex", self._target["color"])
        
    def set_shaders(self):
        self._target_depth.set_shader(self.load_plugin_shader("DownscaleDepth.frag.glsl"))
        self._target.set_shader(self.load_plugin_shader("AOSample.frag.glsl"))
        self._target_upscale.set_shader(self.load_plugin_shader("AOUpscale.frag.glsl"))

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
