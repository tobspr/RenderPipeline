
from panda3d.core import Texture, Vec3

from direct.gui.DirectScrolledFrame import DirectScrolledFrame
from direct.gui.DirectFrame import DirectFrame

from ..Util.FunctionDecorators import protected
from ..Util.Generic import rgbFromString
from DraggableWindow import DraggableWindow
from BetterOnscreenText import BetterOnscreenText
from BetterOnscreenImage import BetterOnscreenImage

from ..Globals import Globals

class PipeViewer(DraggableWindow):

    """ Small tool which displays the order of the graphics pipe """

    stageMgr = None

    @classmethod
    def registerStageMgr(self, mgr):
        self.stageMgr = mgr

    def __init__(self, pipeline):
        DraggableWindow.__init__(self, width=1300, height=900, title="Pipe Inspector")
        self.pipeline = pipeline
        self.scrollWidth = 8000
        self.scrollHeight = 2000
        self.created = False
        self._createComponents()
        self.hide()

    def toggle(self):
        """ Toggles the pipe viewer """        
        if self.visible:
            Globals.base.taskMgr.remove("UpdatePipeViewer")
            self.hide()
        else:
            Globals.base.taskMgr.add(self.updateTask, "UpdatePipeViewer")
            if not self.created:
                self._populateContent()
            self.show()
    
    def updateTask(self, task=None):
        """ Updates the viewer """
        scrollValue = self._contentFrame.horizontalScroll["value"]
        scrollValue *= 2.45
        self.pipeDescriptions.setX(scrollValue * 2759.0 )

        return task.cont

    @protected
    def _populateContent(self):
        """ Reads the pipes and stages from the stage manager and renders those """
        self.created = True
        self.pipeNode = self._contentNode.attachNewNode("pipes")
        self.pipeNode.setScale(1, 1, -1)
        self.stageNode = self._contentNode.attachNewNode("stages")
        currentPipes = []

        pipePixelSize = 3

        # Generate stages
        for offs, stage in enumerate(self.stageMgr.stages):
            node = self._contentNode.attachNewNode("stage")
            node.setPos(220 + offs * 200.0, 0, 20)
            node.setScale(1, 1, -1)
            bg = DirectFrame(parent=node, frameSize=(10, 150, 0, -3600), frameColor=(0.2,0.2,0.2,1))
            stageHeader = BetterOnscreenText(text=str(stage.getName().replace("Stage", "")), parent=node, x=20, y=25, size=15)
            
            for outputPipe, pipeTex in stage.getProducedPipes().iteritems():
                pipeIdx = 0
                r, g, b = rgbFromString(outputPipe)
                if outputPipe in currentPipes:
                    pipeIdx = currentPipes.index(outputPipe)
                else:
                    currentPipes.append(outputPipe)
                    pipeIdx = len(currentPipes) - 1
                    pipeLine = DirectFrame(parent=node, frameSize=(0, 8000, pipePixelSize/2, -pipePixelSize/2), 
                        frameColor=(r, g, b, 1), pos=(10, 1, -95 - pipeIdx * 110.0) )

                w = 160
                h = Globals.base.win.getYSize() / float(Globals.base.win.getXSize()) * w
                pipeBg = DirectFrame(parent=node, 
                    frameSize=(-pipePixelSize, w+pipePixelSize, h/2 + pipePixelSize, -h/2 - pipePixelSize), 
                    frameColor=(r, g, b, 1), pos=(0, 1, -95 - pipeIdx * 110.0))

                if pipeTex.getZSize() > 1:
                    self.debug("Ignoring 3D image", pipeTex.getName())
                    continue

                if pipeTex.getTextureType() == Texture.TTBufferTexture:
                    self.debug("Ignoring texture buffer", pipeTex.getName())
                    continue

                img = BetterOnscreenImage(image=pipeTex, parent=node, x=0, y=50 + pipeIdx * 110.0, 
                    w=w, h=h, anyFilter=False, transparent=False)

            for inputPipe in stage.getInputPipes():
                idx = currentPipes.index(inputPipe)
                r, g, b = rgbFromString(inputPipe)
                marker = DirectFrame(parent=node, frameSize=(0, 10, 40, -40), frameColor=(r, g, b, 1),
                    pos=(5, 1, -95 - idx *110.0))

        self.pipeDescriptions = self._contentNode.attachNewNode("pipeDescriptions")
        self.pipeDescriptions.setScale(1, 1, -1)

        # Generate the pipe descriptions
        for idx, pipe in enumerate(currentPipes):
            r, g, b = rgbFromString(pipe)
            pipeBg = DirectFrame(parent=self.pipeDescriptions, frameSize=(0, 180, -90, -140), 
                frameColor=(r, g, b, 1.0), pos=(0, 1, -idx*110.0))
            pipeHeader = BetterOnscreenText(parent=self.pipeDescriptions, text=pipe, 
                x=20, y=120 + idx*110, size=15, color=Vec3(0.2, 0.2, 0.2))


    @protected
    def _createComponents(self):
        """ Internal method to create the window components """
        DraggableWindow._createComponents(self)

        self._contentFrame = DirectScrolledFrame(
            frameSize=(0, self.width - 40, 0, self.height - 80),
            canvasSize=(0, self.scrollWidth, 0, self.scrollHeight),
            autoHideScrollBars=False,
            scrollBarWidth=20.0,
            frameColor=(0, 0, 0, 0),
            verticalScroll_relief=False,
            horizontalScroll_relief=False,
            # horizontalScroll_incButton_relief=False,
            # horizontalScroll_decButton_relief=False,
            # horizontalScroll_thumb_relief=False,
            parent=self._node,
            pos=(20, 1, -self.height + 20)
            )
        self._contentNode = self._contentFrame.getCanvas().attachNewNode("PipeComponents")
        self._contentNode.setScale(1, 1, -1)
        self._contentNode.setZ(self.scrollHeight)
        # self._contentNode.setX(-self.scrollWidth)
