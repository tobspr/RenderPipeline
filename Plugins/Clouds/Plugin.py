# Load the plugin api
from .. import *

from CloudStage import CloudStage

class Plugin(BasePlugin):

    @PluginHook("on_stage_setup")
    def setup_stages(self):

        sprite_tex = Globals.loader.loadTexture(self.get_resource("CloudSprites.png"))
        self._stage = self.create_stage(CloudStage)
        self._stage.set_sprites(sprite_tex)
