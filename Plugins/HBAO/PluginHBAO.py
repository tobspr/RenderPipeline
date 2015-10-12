
from ...Code.PluginAPI.Plugin import Plugin
from ...Code.RenderStage import RenderStage

from HBAOStage import HBAOStage

class PluginHBAO(Plugin):

    NAME = "HBAO"
    DESCRIPTION = """ This plugin adds support for HBAO """

    SETTINGS = {
        "some_setting": 2,
        "some_other_setting": 3,
    }

    def __init__(self, pipeline):
        Plugin.__init__(self, pipeline, "HBAO")
        self._bind_to_hook("on_shader_reload", self.reload_shaders)
        self._bind_to_hook("on_pipeline_create", self.create_stages)

    def create_stages(self):
        pass

    def reload_shaders(self):
        pass

