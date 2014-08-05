
from Globals import Globals

from BetterOnscreenImage import BetterOnscreenImage

from direct.gui.DirectFrame import DirectFrame


class BufferViewerGUI:

    """ Simple gui to view texture buffers for debugging """

    def __init__(self):
        self.parent = Globals.base.pixel2d.attachNewNode("Buffer Viewer GUI")
        self.bg = DirectFrame(parent=self.parent, frameColor=(0, 0, 0, 0),
                              frameSize=(0, 1100, -800, 0), pos=(300, 1, -20))
        self.bgImg = BetterOnscreenImage(image="Data/GUI/BufferViewer.png",
                                         parent=self.bg, x=0, y=0, w=1100,
                                         h=800, transparent=True,
                                         nearFilter=True)
        self.visible = False
        self.parent.hide()
        Globals.base.accept("v", self.toggle)

    def toggle(self):
        self.visible = not self.visible

        if self.visible:
            self.parent.show()
        else:
            self.parent.hide()
