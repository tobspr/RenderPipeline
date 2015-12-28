
from .. import *

class BloomStage(RenderStage):

    required_pipes = ["ShadedScene"]
    required_inputs = []

    def __init__(self, pipeline):
        RenderStage.__init__(self, "BloomStage", pipeline)
        self._num_mips = 8

    def get_produced_pipes(self):
        return {"ShadedScene": self._upsample_targets[-1]["color"]}

    def set_num_mips(self, mip_count):
        self._num_mips = mip_count

    def create(self):
        self._target_extract = self._create_target("Bloom:ExtractBrightSpots")
        self._target_extract.add_color_texture(bits=16)
        self._target_extract.prepare_offscreen_buffer()

        self._target_firefly = self._create_target("Bloom:RemoveFireflies")
        self._target_firefly.add_color_texture(bits=16)
        self._target_firefly.prepare_offscreen_buffer()

        self._target_firefly.set_shader_input("SourceTex", self._target_extract["color"])

        current_target = self._target_firefly["color"]
        self._downsample_targets = []
        self._upsample_targets = []


        # todo: make the amount of passes configurable
        for i in range(self._num_mips):
            scale_multiplier = 2 ** (1 + i)
            target = self._create_target("Bloom:Downsample:Step-" + str(i))
            target.set_size(-scale_multiplier, -scale_multiplier)
            target.add_color_texture(bits=16)
            target.prepare_offscreen_buffer()
            target.set_shader_input("SourceTex", current_target)
            current_target = target["color"]
            self._downsample_targets.append(target)

        for i in range(self._num_mips):
            scale_multiplier = 2 ** (self._num_mips - i - 1)
            target = self._create_target("Bloom:Upsample:Step-" + str(i))
            target.set_size(-scale_multiplier, -scale_multiplier)
            target.add_color_texture(bits=16)
            target.prepare_offscreen_buffer()

            if i == 0:
                target.set_shader_input("FirstUpsamplePass", True)
            else:
                target.set_shader_input("FirstUpsamplePass", False)

            if i == self._num_mips - 1:
                target.set_shader_input("LastUpsamplePass", True)
            else:
                target.set_shader_input("LastUpsamplePass", False)


            target.set_shader_input("SumTex", current_target)
            target.set_shader_input("SourceTex", self._downsample_targets[-i - 1]["color"])
            current_target = target["color"]
            self._upsample_targets.append(target)


    def set_shaders(self):
        self._target_extract.set_shader(self.load_plugin_shader("ExtractBrightSpots.frag.glsl"))
        self._target_firefly.set_shader(self.load_plugin_shader("RemoveFireflies.frag.glsl"))

        downsample_shader = self.load_plugin_shader("BloomDownsample.frag.glsl")
        upsample_shader = self.load_plugin_shader("BloomUpsample.frag.glsl")
        for target in self._downsample_targets:
            target.set_shader(downsample_shader)  
        for target in self._upsample_targets:
            target.set_shader(upsample_shader)  

    def resize(self):
        RenderStage.resize(self)
        self.debug("Resizing pass")

    def cleanup(self):
        RenderStage.cleanup(self)
        self.debug("Cleanup pass")
