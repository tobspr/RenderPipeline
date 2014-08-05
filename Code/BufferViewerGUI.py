
from Globals import Globals
from DebugObject import DebugObject
from BetterOnscreenImage import BetterOnscreenImage
from BetterOnscreenText import BetterOnscreenText
from RenderTargetType import RenderTargetType
from CheckboxWithLabel import CheckboxWithLabel

from panda3d.core import Vec3, Vec4
from direct.gui.DirectFrame import DirectFrame
from direct.interval.IntervalGlobal import Parallel, Func, Sequence


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

        self.texWidth = 173
        self.texHeight = 96
        self.texPadding = 25
        self.pageSize = 5
        self.innerPadding = 10
        self.paddingTop = 40

        self.createComponents()


    def createComponents(self):

        self.bg = DirectFrame(parent=self.parent, frameColor=(0, 0, 0, 0),
                              frameSize=(0, 1200, -800, 0), pos=(255, 1, -20))
        self.bgImg = BetterOnscreenImage(image="Data/GUI/BufferViewer.png",
                                         parent=self.bg, x=0, y=0, w=1200,
                                         h=800, transparent=True,
                                         nearFilter=True)
        self.buffersParent = self.bg.attachNewNode("Buffers")
        self.buffersParent.setPos(0, 0, -50)

        
        toggleAlpha = CheckboxWithLabel(parent=self.bg, x=10, y=50, 
            textSize=15, text="Alpha only", chbChecked=False, 
            chbCallback=self.setAlphaRendering)


    def setAlphaRendering(self, toggle):
        self.debug("show alpha:",toggle)

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

    def renderBuffers(self):
        self.buffersParent.node().removeAllChildren()

        posX = 0
        posY = 0

        for name in self.bufferOrder:

            target = self.buffers[name]

            for targetType in RenderTargetType.All:
                if not target.hasTarget(targetType):
                    continue
                tex = target.getTexture(targetType)

                sizeStr = str(tex.getXSize()) + " x " + str(tex.getYSize())

                if tex.getZSize() != 1:
                    sizeStr += " x " + str(tex.getZSize())

                node = DirectFrame(parent=self.buffersParent, frameColor=(
                    1, 1, 1, 0.2), frameSize=(-self.innerPadding, self.texWidth + self.innerPadding, -self.texHeight - 30 - self.innerPadding, self.innerPadding +15 ))
                node.setPos(
                    20 + posX * (self.texWidth + self.texPadding), 0, -self.paddingTop -22 - posY * (self.texHeight + self.texPadding + 44))

                aspect = tex.getYSize() / float(tex.getXSize())
                computedWidth = self.texWidth
                computedHeight = self.texWidth * aspect

                if computedHeight > self.texHeight:
                    # have to scale tex width instead
                    computedHeight = self.texHeight
                    computedWidth = tex.getXSize() / float(tex.getYSize()) * self.texHeight


                img = BetterOnscreenImage(
                    image=tex, parent=node, x=0, y=30, w=computedWidth, h=computedHeight, transparent=False, nearFilter=False, anyFilter=False)
                txtName = BetterOnscreenText(
                    text=name, x=0, y=0, size=15, parent=node)
                txtSizeFormat = BetterOnscreenText(
                    text=sizeStr, x=0, y=20, size=15, parent=node, color=Vec3(0.2))
                txtTarget = BetterOnscreenText(
                    text=str(targetType), align="right", x=self.texWidth, y=20, size=15, parent=node, color=Vec3(0.2))

                posX += 1
                if posX > self.pageSize:
                    posY += 1
                    posX = 0

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
