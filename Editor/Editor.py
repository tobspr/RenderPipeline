

from Code.DebugObject import DebugObject
from EditorShowbase import EditorShowbase
from EditorGUI import EditorGUI

class Editor(DebugObject):

    def __init__(self):
        DebugObject.__init__(self, "Editor")
        self.showbase = EditorShowbase()
        self.gui = EditorGUI()

    def run(self):
        self.showbase.run()
