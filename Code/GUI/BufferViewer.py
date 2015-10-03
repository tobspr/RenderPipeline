
from functools import partial

from panda3d.core import Texture, Vec3, Shader, Vec2, LVecBase2i
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectScrolledFrame import DirectScrolledFrame
from direct.gui.DirectGui import DGG

from ..Util.DebugObject import DebugObject
from ..Util.Generic import rgbFromString
from ..Globals import Globals
from TexturePreview import TexturePreview
from BetterOnscreenImage import BetterOnscreenImage
from BetterOnscreenText import BetterOnscreenText
from DraggableWindow import DraggableWindow

class BufferViewer(DraggableWindow):

    """ This class provides a view into the buffers to inspect them """

    registeredEntries = []

    @classmethod
    def registerEntry(self, entry):
        """ Adds a new target to the registered entries """
        self.registeredEntries.append(entry)

    @classmethod
    def unregisterEntry(self, entry):
        """ Removes a target from the registered entries """
        if entry in self.registeredEntries:
            self.registeredEntries.remove(entry)

    def __init__(self, pipeline):
        DraggableWindow.__init__(self, width=1400, height=800, title="Buffer Viewer")
        self.pipeline = pipeline
        self.scrollHeight = 3000
        self.stages = []
        self._createShaders()
        self._createComponents()
        self.texPreview = TexturePreview()
        self.texPreview.hide()
        self.hide()

    def toggle(self):
        """ Updates all the buffers and then toggles the buffer viewer """
        if self.visible:
            self._removeComponents()
            self.hide()
        else:
            self._performUpdate()
            self.show()

    
    def _createShaders(self):
        """ Create the shaders to display the textures """
        self.display2DTexShader = Shader.load(Shader.SLGLSL,
            "Shader/GUI/vertex.glsl", "Shader/GUI/display2DTex.glsl")
        self.display3DTexShader = Shader.load(Shader.SLGLSL,
            "Shader/GUI/vertex.glsl", "Shader/GUI/display3DTex.glsl")
        self.display2DTexArrayShader = Shader.load(Shader.SLGLSL,
            "Shader/GUI/vertex.glsl", "Shader/GUI/display2DTexArray.glsl")
        self.displayBufferTexShader = Shader.load(Shader.SLGLSL,
            "Shader/GUI/vertex.glsl", "Shader/GUI/displayBufferTex.glsl")

    
    def _createComponents(self):
        """ Creates the window components """
        DraggableWindow._createComponents(self)

        self._contentFrame = DirectScrolledFrame(
            frameSize=(0, self.width - 40, 0, self.height - 80),
            canvasSize=(0, self.width - 80, 0, self.scrollHeight),
            autoHideScrollBars=False,
            scrollBarWidth=20.0,
            frameColor=(0, 0, 0, 0),
            verticalScroll_relief=False,
            horizontalScroll_relief=False,
            horizontalScroll_incButton_relief=False,
            horizontalScroll_decButton_relief=False,
            horizontalScroll_thumb_relief=False,
            parent=self._node,
            pos=(20, 1, -self.height + 20)
            )
        self._contentNode = self._contentFrame.getCanvas().attachNewNode("BufferComponents")
        self._contentNode.setScale(1, 1, -1)
        self._contentNode.setZ(self.scrollHeight)

    
    def _removeComponents(self):
        """ Removes all components of the buffer viewer """
        self._contentNode.removeChildren()
        self.texPreview.hide()

    
    def _performUpdate(self):
        """ Collects all entries, extracts their images and updates the render """

        # Collect texture stages
        self.stages = []
        for entry in self.registeredEntries:
            if isinstance(entry, Texture):
                self.stages.append(entry)
            # Cant use isinstance or we get circular references
            elif str(entry.__class__).endswith("RenderTarget"):
                for target in entry.getAllTargets():
                    self.stages.append(entry.getTarget(target))
            # Cant use isinstance or we get circular references
            elif str(entry.__class__).endswith("Image"):
                self.stages.append(entry.tex)
            else:
                self.warn("Unrecognized instance!", entry.__class__)

        self._renderStages()

    
    def _onTextureHovered(self, hoverFrame, evt=None):
        """ Internal method when a texture is hovered """
        hoverFrame["frameColor"] = (0, 0, 0, 0.1)

    
    def _onTextureBlurred(self, hoverFrame, evt=None):
        """ Internal method when a texture is blurred """
        hoverFrame["frameColor"] = (0, 0, 0, 0)

    
    def _onTextureClicked(self, texHandle, evt=None):
        """ Internal method when a texture is blurred """
        self.texPreview.present(texHandle)

    
    def _renderStages(self):
        """ Renders the stages to the window """

        self._removeComponents()
        entriesPerRow = 5
        aspect = Globals.base.win.getYSize() / float(Globals.base.win.getXSize())
        entryWidth = 255
        entryHeight = (entryWidth-20) * aspect + 55

        for index, stageTex in enumerate(self.stages):
            stageName = stageTex.getName()
            stagePrefix = "-".join(stageName.split("-")[:-1]) if "-" in stageName else stageName

            xoffs = index % entriesPerRow
            yoffs = index / entriesPerRow

            node = self._contentNode.attachNewNode("Preview")
            node.setSz(-1)
            node.setPos(30 + xoffs * entryWidth, 1, yoffs * entryHeight)

            r,g,b = rgbFromString(stagePrefix, minBrightness=0.4)

            frame = DirectFrame(parent=node, frameSize=(0, entryWidth - 10, 0, -entryHeight + 10), 
                frameColor=(r, g, b, 1.0),
                pos=(0, 0, 0))

            frameHover = DirectFrame(parent=node, frameSize=(0, entryWidth - 10, 0, -entryHeight + 10), 
                frameColor=(0, 0, 0, 0),
                pos=(0, 0, 0), state=DGG.NORMAL)
            frameHover.bind(DGG.ENTER, partial(self._onTextureHovered, frameHover))
            frameHover.bind(DGG.EXIT, partial(self._onTextureBlurred, frameHover))
            frameHover.bind(DGG.B1PRESS, partial(self._onTextureClicked, stageTex))
            # frameHover.hide()

            caption = BetterOnscreenText(text=stageName, x=10, y=26, parent=node, size=15, color=Vec3(0.2))

            # Scale image so it always fits
            w, h = stageTex.getXSize(), stageTex.getYSize()
            scaleX = float(entryWidth-30) / max(1, w)
            scaleY = float(entryHeight-60) / max(1, h)
            scaleFactor = min(scaleX, scaleY)

            if stageTex.getTextureType() == Texture.TTBufferTexture:
                scaleFactor = 1
                w = entryWidth - 30
                h = entryHeight - 60

            preview = BetterOnscreenImage(image=stageTex, w=scaleFactor*w, h=scaleFactor*h, 
                anyFilter=False, parent=node, x=10, y=40, transparent=False)

            if stageTex.getZSize() <= 1:
                if stageTex.getTextureType() == Texture.TTBufferTexture:
                    preview.setShader(self.displayBufferTexShader)
                    preview.setShaderInput("viewSize", LVecBase2i(int(scaleFactor*w), int(scaleFactor*h)) )
                else:
                    preview.setShader(self.display2DTexShader)
            else:
                if stageTex.getTextureType() == Texture.TT2dTextureArray:
                    preview.setShader(self.display2DTexArrayShader)
                else:
                    preview.setShader(self.display3DTexShader)
