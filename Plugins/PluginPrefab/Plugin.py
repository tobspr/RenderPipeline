
# Load plugin api
from .. import *

# Load some plugin classes here

# Create the main plugin
class Plugin(BasePlugin):

    NAME = "PluginPrefab"
    DESCRIPTION = """ This plugin can be used as a prefab for other plugins """
    SETTINGS = {
        "some_setting":         PS_Int(0, 5, value=1),
        "some_other_setting":   PS_Float(0.5, 2.0, runtime=True),
        "some_enum":            PS_Enum("Value1", "Value2", "Value3", value="Value2"),
    }

    def __init__(self, pipeline):
        BasePlugin.__init__(self, pipeline)

    @PluginHook("on_pipeline_created")
    def init(self):
        pass

    @PluginHook("on_shader_create")
    def create_shaders(self):
        pass

    @SettingChanged("some_setting")
    def update_some_setting(self):
        pass

