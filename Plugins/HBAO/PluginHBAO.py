
from ...Code.PluginAPI.Plugin import Plugin
from ...Code.PluginAPI.PluginSettings import PluginSettingInt, PluginSettingEnum, PluginSettingFloat

from ...Code.RenderStage import RenderStage

from .HBAOStage import HBAOStage

class PluginHBAO(Plugin):

    NAME = "HBAO"
    DESCRIPTION = """ This plugin adds support for HBAO """

    SETTINGS = {
        "some_setting": PluginSettingInt(min_value=0, max_value=5),
        "some_other_setting": PluginSettingFloat(min_value=0.5, max_value=2.0, runtime=True),
        "some_enum": PluginSettingEnum("Value1", "Value2", "Value3", selected="Value2"),
    }

    def __init__(self, pipeline):
        Plugin.__init__(self, pipeline, "HBAO")

    @Plugin.Hook("on_shader_create")
    def create_stages(self):
        pass

    @Plugin.Hook("on_pipeline_create")
    def reload_shaders(self):
        pass

