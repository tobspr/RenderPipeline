
# Load plugin api
from .. import *

# Load some plugin classes
from .HBAOStage import HBAOStage

# Create the main plugin
class Plugin(BasePlugin):

    NAME = "HBAO"
    DESCRIPTION = """ This plugin adds support for HBAO """
    SETTINGS = {
        "some_setting":         PluginSettingInt(0, 5, value=1),
        "some_other_setting":   PluginSettingFloat(0.5, 2.0, runtime=True),
        "some_enum":            PluginSettingEnum("Value1", "Value2", "Value3", value="Value2"),
    }

    def __init__(self, pipeline):
        BasePlugin.__init__(self, pipeline)

    @PluginHook("on_shader_create")
    def create_stages(self):
        pass

    @PluginHook("on_pipeline_created")
    def reload_shaders(self):
        pass

