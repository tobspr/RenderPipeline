

from panda3d.core import Vec3, PerspectiveLens
from direct.gui.DirectFrame import DirectFrame
from direct.interval.IntervalGlobal import Parallel, Sequence

from BetterOnscreenImage import BetterOnscreenImage
from BufferViewer import BufferViewer
from PipeViewer import PipeViewer

from ..Util.DebugObject import DebugObject
from ..Globals import Globals


class OnscreenDebugger(DebugObject):

    """ This class manages the onscreen gui """

    def __init__(self, pipeline):
        DebugObject.__init__(self, "OnscreenDebugger")
        self.debug("Creating debugger")
        self.pipeline = pipeline

        self.fullscreenNode = Globals.base.pixel2d.attachNewNode("PipelineDebugger")
        self._createComponents()
        self._initKeybindings()

    
    def _createComponents(self):
        """ Creates the gui components """

        # Component values
        self.debuggerWidth = 380
        self.debuggerHeight = 800

        # Create states
        self.debuggerVisible = False

        # Create intervals
        self.debuggerInterval = None

        # Create the actual GUI
        self._createDebugger()
        self._createTopbar()
        self.bufferViewer = BufferViewer(self.pipeline)
        self.pipeViewer = PipeViewer(self.pipeline)

    
    def _createTopbar(self):
        """ Creates the topbar """
        self.logoBackground = DirectFrame(parent=self.fullscreenNode, frameSize=(1.0, 0, 0, -1),
            pos=(40, 0, -10), frameColor=(0.094, 0.094, 0.094, 1), scale=(100, 0, 100))
        self.pipelineLogo = BetterOnscreenImage(image="Data/GUI/OnscreenDebugger/PipelineLogo.png", 
            x=40, y=10, parent=self.fullscreenNode)
        self.pipelineLogoText = BetterOnscreenImage(image="Data/GUI/OnscreenDebugger/PipelineLogoText.png", 
            x=144, y=48, parent=self.fullscreenNode)
        self.topBar = DirectFrame(parent=self.fullscreenNode, frameSize=(5000, 0, 0, -22),
            pos=(0, 0, 0), frameColor=(0.094,0.094,0.094,1))

        # Hide the logo text in the beginning
        self.pipelineLogoText.setPos(150, -100)

    
    def _createDebugger(self):
        """ Creates the debugger contents """

        self.debuggerNode = self.fullscreenNode.attachNewNode("DebuggerNode")
        self.debuggerNode.setZ(self.debuggerHeight)
        self.debuggerBg = DirectFrame(parent=self.debuggerNode, frameSize=(self.debuggerWidth, 0, 0, -self.debuggerHeight + 20),
            pos=(40, 0, 0), frameColor=(0.05, 0.05, 0.05, 1))
        self.debuggerBgBottom = DirectFrame(parent=self.debuggerNode, frameSize=(self.debuggerWidth, 0, 0, -15),
            pos=(40, 0, -self.debuggerHeight + 20), frameColor=(0.05, 0.05, 0.05, 1))

    
    def _initKeybindings(self):
        """ Inits the debugger keybindings """
        Globals.base.accept("g", self._toggleDebugger)
        Globals.base.accept("v", self.bufferViewer.toggle)
        Globals.base.accept("c", self.pipeViewer.toggle)

    
    def _toggleDebugger(self):
        """ Internal method to hide or show the debugger """
        if self.debuggerInterval is not None:
            self.debuggerInterval.finish()

        if self.debuggerVisible:
            # Hide Debugger
            self.debuggerInterval = Sequence(
                Parallel(
                self.debuggerNode.posInterval(0.16, Vec3(0, 0, self.debuggerHeight), Vec3(0, 0, 0), blendType="easeInOut"),
                self.pipelineLogoText.posInterval(0.16, self.pipelineLogoText.initialPos + Vec3(0, 0, 100), self.pipelineLogoText.initialPos, blendType="easeInOut"),
                ),
                Parallel(
                    self.pipelineLogo.hprInterval(0.2, Vec3(0, 0, 0), Vec3(0, 0, 270), blendType="easeInOut"),
                    self.logoBackground.scaleInterval(0.2, Vec3(103, 0, 100), Vec3( self.debuggerWidth, 0, 100), blendType = "easeInOut"),
                ),
                )

        else:
            # Show debugger
            self.debuggerInterval = Sequence(
                Parallel(
                    self.pipelineLogo.hprInterval(0.2, Vec3(0, 0, 270), Vec3(0, 0, 0), blendType="easeInOut"),
                    self.logoBackground.scaleInterval(0.2, Vec3(self.debuggerWidth, 0, 100), Vec3( 103, 0, 100), blendType = "easeInOut"),
                ),
                Parallel(
                self.pipelineLogoText.posInterval(0.16, self.pipelineLogoText.initialPos, self.pipelineLogoText.initialPos  + Vec3(0, 0, 100), blendType="easeInOut"),
                self.debuggerNode.posInterval(0.16, Vec3(0, 0, 0), Vec3(0, 0, self.debuggerHeight), blendType="easeInOut")
                ),
                )            

        self.debuggerInterval.start()
        self.debuggerVisible = not self.debuggerVisible

