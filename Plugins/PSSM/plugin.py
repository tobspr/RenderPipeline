

from PluginAPI.Plugin import Plugin


class Plugin_PSSM(Plugin):

    NAME = "Directional Light with PSSM Shadows"
    DESCRIPTION = """ This plugin adds support for a directional light with 
    pssm shadows """

    def __init__(self):
        Plugin.__init__(self, "PSSM")

    def create(self):
        Plugin.create(self)

    def update(self):
        Plugin.update(self)

    def destroy(self):
        Plugin.destroy(self)

