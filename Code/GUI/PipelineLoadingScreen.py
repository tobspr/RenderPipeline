

from panda3d.core import Vec3, Vec4, NodePath
from direct.gui.DirectFrame import DirectFrame
from direct.interval.IntervalGlobal import Sequence

from BetterOnscreenText import BetterOnscreenText
from BetterOnscreenImage import BetterOnscreenImage

import random
import math


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

        scaleX = w / 2560.0
        scaleY = h / 1440.0

        imageScale = max(scaleX, scaleY)
        imageW = 2560 * imageScale
        imageH = 1440 * imageScale

        self.bgFrame = DirectFrame(parent=self.node,
                                   frameColor=(0.9, 0.9, 0.9, 1.0),
                                   frameSize=(0, w, -h, 0))



        self.font = loader.loadFont("Data/Font/Roboto-Light.ttf")
        self.fontHighRes = loader.loadFont("Data/Font/Roboto-Thin.ttf")
        self.fontHighRes.setPixelsPerUnit(120)
        

        xOffs = (w - imageW) / 2.0
        yOffs = (h - imageH) / 2.0


        self.bgImage = BetterOnscreenImage(image="Data/GUI/LoadingScreen.png", parent=self.node, w=imageW, h=imageH, x=xOffs, y=yOffs)



        self.points = []
        self.pointAngles = [10, 25, 40, 51, 80, 103, 130, 152, 170, 198, 210, 231, 250, 274, 290, 310, 328, 352]

        random.seed(491)

        for angle in self.pointAngles:
            scale = 180.0
            point = BetterOnscreenImage(image="Data/GUI/LoadingScreenPoint.png", parent=self.node, w=scale, h=scale, x=(w-scale)/2, y=(h-scale)/2, nearFilter=False)
            point._node.setR(angle)

            scaleZ = scale * (1.0 + random.random() * 1.2) * (1.0 + 0.6 * abs(math.cos(angle / 180.0 * math.pi)))
            point._node.setScale(scaleZ, scale, scale)
            sFrom, sTo = 0.7, 1.2

            seq = Sequence(
                    point._node.scaleInterval(2.0 + random.random(), Vec3(scaleZ * sFrom, scale,scale), startScale=Vec3(scaleZ*sTo, scale,scale), blendType="easeInOut"),
                    point._node.scaleInterval(2.0 + random.random(), Vec3(scaleZ * sTo, scale,scale), startScale=Vec3(scaleZ*sFrom, scale,scale), blendType="easeInOut"),
                )
            seq.loop()
            self.points.append(point)






        cr = 212
        ct = 0

        self.circlePart1 = BetterOnscreenImage(image="Data/GUI/LoadingCirclePart.png", parent=self.node, w=cr, h=cr, x=(w-cr) / 2, y = (h-cr) / 2 - ct)
        self.circlePart2 = BetterOnscreenImage(image="Data/GUI/LoadingCirclePart.png", parent=self.node, w=cr, h=cr, x=(w-cr) / 2, y = (h-cr) / 2 - ct)
        self.circlePart3 = BetterOnscreenImage(image="Data/GUI/LoadingCirclePart.png", parent=self.node, w=cr, h=cr, x=(w-cr) / 2, y = (h-cr) / 2 - ct)
        self.circlePart4 = BetterOnscreenImage(image="Data/GUI/LoadingCirclePart.png", parent=self.node, w=cr, h=cr, x=(w-cr) / 2, y = (h-cr) / 2 - ct)

        self.circleBg = BetterOnscreenImage(image="Data/GUI/LoadingCircleBgBlack.png", parent=self.node, w=180, h=180, x=(w-180) / 2, y = (h-180) / 2 - ct)

        self.logoImage = BetterOnscreenImage(image="Data/GUI/RPIcon.png", parent=self.node, w=316, h=316, x=(w - 316) /2, y = (h-316) / 2 - ct)

        self.loadingDescText = BetterOnscreenText(text="50%".upper(), parent=self.node, x=w-50, y=h - 95, size=90, align="right", color=Vec4(0.9,0.9,0.9,0.5), mayChange=True, font=self.fontHighRes)
        self.loadingText = BetterOnscreenText(text="Compiling Shaders".upper(), parent=self.node, x=w-50, y=h - 65, size=18, align="right", color=Vec4(117/255.0, 175/255.0, 65/255.0,0.2), mayChange=True, font=self.font)
        self.versionText = BetterOnscreenText(text="Rendering Pipeline 1.0.1".upper(), parent=self.node, x=50, y=80, size=30, align="left", color=Vec4(0.9,0.9,0.9,0.5), mayChange=False, font=self.font)
        self.linkText = BetterOnscreenText(text="github.com/tobspr/renderpipeline".upper(), parent=self.node, x=50, y=105, size=18, align="left", color=Vec4(117/255.0, 175/255.0, 65/255.0,0.2), mayChange=False, font=self.font)

        self.loadingBarBG = DirectFrame(parent=self.node,
                                   frameColor=Vec4(0.2,0.2,0.2,0.8),
                                   frameSize=(0, w, -3, 0),
                                   pos=(0, 0, -h + 30))
        self.loadingBar = DirectFrame(parent=self.node,
                                   frameColor=Vec4(117/255.0, 175/255.0, 65/255.0,0.8),
                                   frameSize=(0, w, -3, 0),
                                   pos=(0, 0, -h + 30))

        self.circlePart2._node.setR(180)
        self.circlePart3._node.setR(90)
        self.circlePart4._node.setR(-90)
        # self.circlePart1._node.setColorScale(Vec4(103/255.0,167/255.0,53/255.0,1.0))
        self.circlePart1._node.setColorScale(Vec4(0.5,1.0,1.0,0.5))
        self.circlePart2._node.setColorScale(Vec4(1.0,0.5,1.0,0.5))
        self.circlePart3._node.setColorScale(Vec4(1.0,1.0,0.5,0.5))
        self.circlePart4._node.setColorScale(Vec4(0.5,0.5,1.0,0.5))

        self.circlePart1.hide()
        self.circlePart2.hide()
        self.circlePart3.hide()
        self.circlePart4.hide()


        interval1 = self.circlePart1.hprInterval(2.1, Vec3(0,0,360))
        interval1.loop()
        interval2 = self.circlePart2.hprInterval(2.3, Vec3(0,0,-180))
        interval2.loop()
        interval3 = self.circlePart3.hprInterval(2.5, Vec3(0,0,-270))
        interval3.loop()
        interval4 = self.circlePart4.hprInterval(2.7, Vec3(0,0,270))
        interval4.loop()
        self.showbase.graphicsEngine.renderFrame()

        self.setStatus("Initializing", 5)

    def setStatus(self, status, percentage=0):
        """ Sets the current loading status """
        self.loadingText.setText(status.upper())
        self.loadingDescText.setText(str(percentage) + "%")
        self.showbase.graphicsEngine.renderFrame()

        w = self.showbase.win.getXSize()
        l = percentage / 100.0 * w
        self.loadingBar.setSx(percentage / 100.0)
        # self.loadingBar.

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
