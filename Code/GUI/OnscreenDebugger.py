

from panda3d.core import Vec3
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
        self._pipeline = pipeline

        self._fullscreen_node = Globals.base.pixel2d.attach_new_node(
            "PipelineDebugger")
        self._create_components()
        self._init_keybindings()

    def _create_components(self):
        """ Creates the gui components """

        # Component values
        self._debugger_width = 380
        self._debugger_height = 800

        # Create states
        self._debugger_visible = False

        # Create intervals
        self._debugger_interval = None

        # Create the actual GUI
        self._create_debugger()
        self._create_topbar()
        self._buffer_viewer = BufferViewer(self._pipeline)
        self._pipe_viewer = PipeViewer(self._pipeline)

    def _create_topbar(self):
        """ Creates the topbar """
        self._pipeline_logo = BetterOnscreenImage(image="Data/GUI/OnscreenDebugger/PipelineLogo.png", 
                                                  x=40, y=20,
                                                  parent=self._fullscreen_node)
        self._pipeline_logo_text = BetterOnscreenImage(image="Data/GUI/OnscreenDebugger/PipelineLogoText.png", 
                                                       x=144, y=48,
                                                       parent=self._fullscreen_node)
        self._topbar = DirectFrame(parent=self._fullscreen_node,
                                   frameSize=(5000, 0, 0, -22),
                                   pos=(0, 0, 0),
                                   frameColor=(0.094, 0.094, 0.094, 1))
        # Hide the logo text in the beginning
        self._pipeline_logo_text.set_pos(150, -100)

    def _create_debugger(self):
        """ Creates the debugger contents """

        self._debugger_node = self._fullscreen_node.attach_new_node("DebuggerNode")
        self._debugger_node.set_z(self._debugger_height)
        self._debugger_bg = DirectFrame(parent=self._debugger_node,
                                        frameSize=(self._debugger_width, 0, 0,
                                                   -self._debugger_height + 20),
                                        pos=(40, 0, 0),
                                        frameColor=(0.05, 0.05, 0.05, 1))
        self._debugger_bg_bottom = DirectFrame(parent=self._debugger_node,
                                               frameSize=(self._debugger_width, 0, 0, -15),
                                               pos=(40, 0, -self._debugger_height + 20),
                                               frameColor=(0.05, 0.05, 0.05, 1))

    def _init_keybindings(self):
        """ Inits the debugger keybindings """
        Globals.base.accept("g", self._toggle_debugger)
        Globals.base.accept("v", self._buffer_viewer.toggle)
        Globals.base.accept("c", self._pipe_viewer.toggle)

    def _toggle_debugger(self):
        """ Internal method to hide or show the debugger """
        if self._debugger_interval is not None:
            self._debugger_interval.finish()

        if self._debugger_visible:
            # Hide Debugger
            self._debugger_interval = Sequence(
                Parallel(
                    self._debugger_node.posInterval(0.16,
                                                     Vec3(0, 0, self._debugger_height),
                                                     Vec3(0, 0, 0), blendType="easeInOut"),
                    self._pipeline_logo_text.pos_interval(0.16,
                                                          self._pipeline_logo_text.get_initial_pos() + Vec3(0, 0, 100),
                                                          self._pipeline_logo_text.get_initial_pos, blendType="easeInOut"),
                    self._pipeline_logo.hpr_interval(0.2, Vec3(0, 0, 0),
                                                     Vec3(0, 0, 90),
                                                     blendType="easeInOut"),
                ))
        else:
            # Show debugger
            self._debugger_interval = Sequence(
                Parallel(
                    self._pipeline_logo.hpr_interval(0.2, Vec3(0, 0, 90),
                                                     Vec3(0, 0, 0),
                                                     blendType="easeInOut"),
                    self._pipeline_logo_text.pos_interval(0.16, 
                                                          self._pipeline_logo_text.get_initial_pos(),
                                                          self._pipeline_logo_text.get_initial_pos()  + Vec3(0, 0, 100),
                                                          blendType="easeInOut"),
                    self._debugger_node.posInterval(0.16, Vec3(0, 0, 0),
                                                     Vec3(0, 0, self._debugger_height),
                                                     blendType="easeInOut")
                ))
        self._debugger_interval.start()
        self._debugger_visible = not self._debugger_visible
