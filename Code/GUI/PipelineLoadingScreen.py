

from panda3d.core import Vec3, Vec4
from direct.gui.DirectFrame import DirectFrame


from BetterOnscreenText import BetterOnscreenText
from BetterOnscreenImage import BetterOnscreenImage


class PipelineLoadingScreen:


    """ Simple loading screen which shows the pipeline logo while loading """

    def __init__(self, showbase):
        self.showbase = showbase

    def render(self):
        """ Inits the loading screen, creating the gui """    
        self.node = self.showbase.pixel2d.attachNewNode("Loading Screen")
        self.node.setBin("fixed", 10)
        self.node.setDepthTest(False)

        self.showbase.setFrameRateMeter(False)

        w, h = self.showbase.win.getXSize(), self.showbase.win.getYSize()

        self.bgFrame = DirectFrame(parent=self.node,
                                   frameColor=(0.9, 0.9, 0.9, 1.0),
                                   frameSize=(0, w, -h, 0))



        self.font = loader.loadFont("Data/Font/Multicolore.otf")

        xOffs = (w - 1920) / 2.0
        yOffs = (h - 1080) / 2.0

        self.bgImage = BetterOnscreenImage(image="Data/GUI/LoadingScreen.png", parent=self.node, w=1920, h=1080, x=xOffs, y=yOffs)

        self.logoImage = BetterOnscreenImage(image="Data/GUI/RPIcon.png", parent=self.node, w=316, h=316, x=(w - 316) /2, y = (h-316) / 2 - 50)

        self.loadingText = BetterOnscreenText(text="Compiling Shaders ...", parent=self.node, x=w/2, y=h - 50, size=25, align="center", color=Vec4(0.9,0.9,0.9,0.5), mayChange=True, font=self.font)
        self.showbase.graphicsEngine.renderFrame()

    def setStatus(self, status):
        """ Sets the current loading status """
        self.loadingText.setText(status)
        self.showbase.graphicsEngine.renderFrame()

    def _cleanup(self, task):
        """ Internal method to remove the loading screen """
        self.node.removeNode()
        self.showbase.setFrameRateMeter(True)
    
    def hide(self):
        """ Tells the loading screen to hide as soon as possible """
        self.showbase.taskMgr.doMethodLater(0.1, self._cleanup, "cleanupLoadingScreen")
