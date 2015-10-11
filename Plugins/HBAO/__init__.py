
from ...Code.PluginAPI.Plugin import Plugin
from ...Code.Util.RenderTarget import RenderTarget


class Plugin_HBAO(Plugin):

    NAME = "HBAO"
    DESCRIPTION = """ This plugin adds support for HBAO """

    def __init__(self):
        Plugin.__init__(self, "HBAO")
        self._bind_to_hook("on_shader_reload", self.reload_shaders)

    def create(self):
        Plugin.create(self)

    def update(self):
        Plugin.update(self)

    def destroy(self):
        Plugin.destroy(self)

    def reload_shaders(self):
        pass
