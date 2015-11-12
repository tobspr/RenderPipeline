# Load the plugin api
from .. import *

# Load your additional plugin classes here, if required

class Plugin(BasePlugin):

    def __init__(self, pipeline):
        BasePlugin.__init__(self, pipeline)

    @PluginHook("on_stage_setup")
    def setup_stages(self):
        """ This method gets called when the pipeline setups the render
        stages. You should create your custom stages here """

    @PluginHook("on_pipeline_created")
    def on_created(self):
        """ This method gets called after the pipeline finished the setup,
        and is about to start rendering """

    @SettingChanged("some_setting")
    def update_some_setting(self):
        """ This method gets called when the setting "some_setting"
        of your plugin gets called. You should do all work to update required
        inputs etc. yourself. """
