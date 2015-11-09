
# Load the plugin api
from .. import *

# Load some plugin classes here


class Plugin(BasePlugin):

    def __init__(self, pipeline):
        BasePlugin.__init__(self, pipeline)

    @PluginHook("on_stage_setup"):
    def setup_stages(self):
        pass

    @PluginHook("on_pipeline_created")
    def init(self):
        pass

    @SettingChanged("some_setting")
    def update_some_setting(self):
        pass

