

from panda3d.core import Vec3, Vec4, NodePath
from direct.gui.DirectFrame import DirectFrame


from BetterOnscreenText import BetterOnscreenText
from BetterOnscreenImage import BetterOnscreenImage


class PipelineLoadingScreen:


    """ Simple loading screen which shows the pipeline logo while loading """

    def __init__(self, showbase):
        self.showbase = showbase
        self.active = False

    def render(self):
        """ Inits the loading screen, creating the gui """    
        self.node = self.showbase.pixel2dp.attachNewNode("Loading Screen")
        self.node.setBin("fixed", 10)
        self.node.setDepthTest(False)

        self.showbase.setFrameRateMeter(False)

        w, h = self.showbase.win.getXSize(), self.showbase.win.getYSize()

        self.bgFrame = DirectFrame(parent=self.node,
                                   frameColor=(0.9, 0.9, 0.9, 1.0),
                                   frameSize=(0, w, -h, 0))



        self.font = loader.loadFont("Data/Font/Multicolore.otf")

        

        xOffs = (w - 2560) / 2.0
        yOffs = (h - 1440) / 2.0

        self.bgImage = BetterOnscreenImage(image="Data/GUI/LoadingScreen.png", parent=self.node, w=2560, h=1440, x=xOffs, y=yOffs)

        cr = 212

        self.circlePart1 = BetterOnscreenImage(image="Data/GUI/LoadingCirclePart.png", parent=self.node, w=cr, h=cr, x=(w-cr) / 2, y = (h-cr) / 2 - 50)
        self.circlePart2 = BetterOnscreenImage(image="Data/GUI/LoadingCirclePart.png", parent=self.node, w=cr, h=cr, x=(w-cr) / 2, y = (h-cr) / 2 - 50)
        self.circlePart3 = BetterOnscreenImage(image="Data/GUI/LoadingCirclePart.png", parent=self.node, w=cr, h=cr, x=(w-cr) / 2, y = (h-cr) / 2 - 50)
        self.circlePart4 = BetterOnscreenImage(image="Data/GUI/LoadingCirclePart.png", parent=self.node, w=cr, h=cr, x=(w-cr) / 2, y = (h-cr) / 2 - 50)

        self.circleBg = BetterOnscreenImage(image="Data/GUI/LoadingCircleBg.png", parent=self.node, w=180, h=180, x=(w-180) / 2, y = (h-180) / 2 - 50)

        self.logoImage = BetterOnscreenImage(image="Data/GUI/RPIcon.png", parent=self.node, w=316, h=316, x=(w - 316) /2, y = (h-316) / 2 - 50)

        self.loadingText = BetterOnscreenText(text="Compiling Shaders ...", parent=self.node, x=w/2, y=h - 50, size=25, align="center", color=Vec4(0.9,0.9,0.9,0.5), mayChange=True, font=self.font)

        self.circlePart2._node.setR(180)
        self.circlePart3._node.setR(90)
        self.circlePart4._node.setR(-90)
        # self.circlePart1._node.setColorScale(Vec4(103/255.0,167/255.0,53/255.0,1.0))
        self.circlePart1._node.setColorScale(Vec4(0.5,1.0,1.0,0.5))
        self.circlePart2._node.setColorScale(Vec4(1.0,0.5,1.0,0.5))
        self.circlePart3._node.setColorScale(Vec4(1.0,1.0,0.5,0.5))
        self.circlePart4._node.setColorScale(Vec4(0.5,0.5,1.0,0.5))


        interval1 = self.circlePart1.hprInterval(1.1, Vec3(0,0,360))
        interval1.loop()
        interval2 = self.circlePart2.hprInterval(1.3, Vec3(0,0,-180))
        interval2.loop()
        interval3 = self.circlePart3.hprInterval(1.5, Vec3(0,0,-270))
        interval3.loop()
        interval4 = self.circlePart4.hprInterval(1.7, Vec3(0,0,270))
        interval4.loop()
        self.showbase.graphicsEngine.renderFrame()

    def setStatus(self, status):
        """ Sets the current loading status """
        self.loadingText.setText(status)
        self.showbase.graphicsEngine.renderFrame()

    def _cleanup(self, task):
        """ Internal method to remove the loading screen """
        self.node.removeNode()
        self.showbase.setFrameRateMeter(True)
    
    def update(self, task):

        if self.active:
            return task.cont

    def hide(self):
        """ Tells the loading screen to hide as soon as possible """
        self.showbase.taskMgr.doMethodLater(0.0, self._cleanup, "cleanupLoadingScreen")
