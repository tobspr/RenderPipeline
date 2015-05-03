
from direct.gui.DirectFrame import DirectFrame


from BetterOnscreenImage import BetterOnscreenImage


class PipelineLoadingScreen:

    """ Simple loading screen which shows the pipeline logo while loading """

    def __init__(self, showbase):
        self.showbase = showbase



    def render(self):
    
        self.node = self.showbase.pixel2d.attachNewNode("Loading Screen")
    

        w, h = self.showbase.win.getXSize(), self.showbase.win.getYSize()

        self.bgFrame = DirectFrame(parent=self.node,
                                   frameColor=(0.9, 0.9, 0.9, 1.0),
                                   frameSize=(0, w, -h, 0))


        xOffs = (w - 1920) / 2.0
        yOffs = (h - 1080) / 2.0

        self.bgImage = BetterOnscreenImage(image="Data/GUI/LoadingScreen.png", parent=self.node, w=1920, h=1080, x=xOffs, y=yOffs)


        self.showbase.graphicsEngine.renderFrame()

    def hide(self):
        self.node.removeNode()