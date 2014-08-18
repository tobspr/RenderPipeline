
from Code.DebugObject import DebugObject

from panda3d.core import *
from direct.showbase.ShowBase import ShowBase

class EditorShowbase(ShowBase, DebugObject):
    
    def __init__(self):
        DebugObject.__init__(self, "EditorShowbase")

        # Load the default prc file
        loadPrcFile("Config/configuration.prc")
        loadPrcFileData("", "window-title RenderPipeline Editor v0.1")

        ShowBase.__init__(self)

        