
import direct.gui.DirectGuiGlobals as DGG

from ..Globals import Globals
from ..DebugObject import DebugObject
from ..RenderTargetType import RenderTargetType
from BetterOnscreenImage import BetterOnscreenImage
from BetterOnscreenText import BetterOnscreenText
from BetterButton import BetterButton
from CheckboxWithLabel import CheckboxWithLabel
from UIWindow import UIWindow
from functools import partial

from panda3d.core import Vec3, Vec4
from direct.gui.DirectFrame import DirectFrame
from direct.interval.IntervalGlobal import Parallel, Func, Sequence


class FakeBuffer:

    """ Small wrapper to allow textures to be viewed in the texture viewer """

    def __init__(self, tex):
        self.tex = tex

    def hasTarget(self, target):
        return target == RenderTargetType.Color

    def getTexture(self, target):
        return self.tex



class BufferViewerGUI(DebugObject):

    """ Simple gui to view texture buffers for debugging """

    buffers = {}
    bufferOrder = []

    def __init__(self, parent):
        DebugObject.__init__(self, "BufferViewer")
        self.parent = parent
        self.parent.setColorScale(0, 0, 0, 0)

        self.visible = False
        self.currentGUIEffect = None
        self.parent.hide()
        Globals.base.accept("v", self.toggle)

        self.window = UIWindow(
            "Buffer Viewer", 1200, 800, parent)

        self.window.getNode().setPos(255, 1, -20)

        self.texWidth = 173
        self.texHeight = 96
        self.texPadding = 25
        self.pageSize = 5
        self.innerPadding = 10
        self.paddingTop = 40

        self.createComponents()

    def createComponents(self):
        self.buffersParent = self.window.getContentNode().attachNewNode(
            "buffers")
        toggleAlpha = CheckboxWithLabel(parent=self.window.getContentNode(), x=10, y=10,
                                        textSize=15, text="Alpha only", chbChecked=False,
                                        chbCallback=self.setAlphaRendering)

    def setAlphaRendering(self, toggle):
        self.debug("show alpha:", toggle)

    @classmethod
    def registerBuffer(self, name, buff):
        self.buffers[name] = buff
        self.bufferOrder.append(name)

    @classmethod
    def unregisterBuffer(self, name):
        if name in self.buffers:
            del self.buffers[name]
            self.bufferOrder.remove(name)
        else:
            print "BufferViewer: Warning: buffer not in dictionary"

    @classmethod
    def registerTexture(self, name, tex):
        fb = FakeBuffer(tex)
        self.registerBuffer(name, fb)

    @classmethod
    def unregisterTexture(self, name):
        self.unregisterBuffer(name)

    def renderBuffers(self):
        self.buffersParent.node().removeAllChildren()

        posX = 0
        posY = 0

        for name in self.bufferOrder:

            target = self.buffers[name]

            if not isinstance(target, FakeBuffer):
                sort1 = target.getInternalRegion().getSort()
                sort2 = target.getRegion().getSort()
                sort3 = target.getInternalBuffer().getSort()
                sort4 = target.getInternalBuffer().getDisplayRegion(0).getSort()
                sortStr = "(" + str(sort3) + ";" + str(sort4) + ")"
            else:
                sortStr = ""

            for targetType in RenderTargetType.All:

                if not target.hasTarget(targetType):
                    continue

                tex = target.getTexture(targetType)

                sizeStr = str(tex.getXSize()) + " x " + str(tex.getYSize())

                if tex.getZSize() != 1:
                    sizeStr += " x " + str(tex.getZSize())

                node = DirectFrame(parent=self.buffersParent, frameColor=(
                    1, 1, 1, 0.2), frameSize=(-self.innerPadding, self.texWidth + self.innerPadding, -self.texHeight - 30 - self.innerPadding, self.innerPadding + 15),
                    state=DGG.NORMAL)
                node.setPos(
                    20 + posX * (self.texWidth + self.texPadding), 0, -self.paddingTop - 22 - posY * (self.texHeight + self.texPadding + 44))

                node.bind(DGG.ENTER, partial(self.onMouseOver, node))
                node.bind(DGG.EXIT, partial(self.onMouseOut, node))
                node.bind(DGG.B1RELEASE, partial(self.showDetail, tex))

                aspect = tex.getYSize() / float(tex.getXSize())
                computedWidth = self.texWidth
                computedHeight = self.texWidth * aspect

                if computedHeight > self.texHeight:
                    # have to scale tex width instead
                    computedHeight = self.texHeight
                    computedWidth = tex.getXSize() / float(tex.getYSize()) * \
                        self.texHeight

                img = BetterOnscreenImage(
                    image=tex, parent=node, x=0, y=30, w=computedWidth, h=computedHeight, transparent=False, nearFilter=False, anyFilter=False)
                txtName = BetterOnscreenText(
                    text=name, x=0, y=0, size=15, parent=node)
                txtSizeFormat = BetterOnscreenText(
                    text=sizeStr + " " + sortStr, x=0, y=20, size=15, parent=node, color=Vec3(0.2))
                txtTarget = BetterOnscreenText(
                    text=str(targetType), align="right", x=self.texWidth, y=20, size=15, parent=node, color=Vec3(0.2))

                posX += 1
                if posX > self.pageSize:
                    posY += 1
                    posX = 0

    # def selectTexture(self, coord, elem, ):
    #     print "Select texture!:",a

    def showDetail(self, tex, coord):
        print "Showing detail:", tex

        availableW = 1180
        availableH = 690

        texW, texH = tex.getXSize(), tex.getYSize()
        aspect = float(texH) / texW

        displayW = availableW
        displayH = displayW * aspect

        if displayH > availableH:
            displayH = availableH
            displayW = displayH / aspect

        self.buffersParent.node().removeAllChildren()

        img = BetterOnscreenImage(
            image=tex, parent=self.buffersParent, x=10, y=40, w=displayW, h=displayH,
            transparent=False, nearFilter=False, anyFilter=False)

        backBtn = BetterButton(self.buffersParent, 150, 2, "Back", callback=self.renderBuffers)

    def onMouseOver(self, node, a):
        node['frameColor'] = (1, 1, 1, 0.4)

    def onMouseOut(self, node, a):
        node['frameColor'] = (1, 1, 1, 0.2)

    def toggle(self):
        self.visible = not self.visible

        self.debug("Toggle buffer viewer")

        if self.currentGUIEffect is not None:
            self.currentGUIEffect.finish()

        if not self.visible:

            self.currentGUIEffect = Sequence(
                self.parent.colorScaleInterval(
                    0.12, Vec4(1, 1, 1, 0),
                    blendType="easeIn"),
                Func(self.parent.hide)

            )
            self.currentGUIEffect.start()

        else:
            self.renderBuffers()
            self.parent.show()
            self.currentGUIEffect = Parallel(
                self.parent.colorScaleInterval(
                    0.12, Vec4(1, 1, 1, 1),
                    blendType="easeIn"),
            )
            self.currentGUIEffect.start()
