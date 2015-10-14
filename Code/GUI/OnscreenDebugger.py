

from panda3d.core import Vec3
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectOptionMenu import DirectOptionMenu
from direct.gui.DirectGuiBase import DGG
from direct.interval.IntervalGlobal import Parallel, Sequence


from .BetterOnscreenImage import BetterOnscreenImage
from .BufferViewer import BufferViewer
from .PipeViewer import PipeViewer
from .BetterOnscreenText import BetterOnscreenText


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

        # When using small resolutions, scale the GUI so its still useable,
        # otherwise the sub-windows are bigger than the main window
        scale_factor = min(1.0, Globals.base.win.get_x_size() / 1800.0)
        self._fullscreen_node.set_scale(scale_factor)

        # Component values
        self._debugger_width = 420
        self._debugger_height = 800

        # Create states
        self._debugger_visible = False

        # Create intervals
        self._debugger_interval = None

        # Create the actual GUI
        self._create_debugger()
        self._create_topbar()
        self._buffer_viewer = BufferViewer(self._pipeline, self._fullscreen_node)
        self._pipe_viewer = PipeViewer(self._pipeline, self._fullscreen_node)

    def _create_topbar(self):
        """ Creates the topbar """
        self._pipeline_logo = BetterOnscreenImage(
            image="Data/GUI/OnscreenDebugger/PipelineLogo.png", x=20, y=20,
            parent=self._fullscreen_node)
        self._pipeline_logo_text = BetterOnscreenImage(
            image="Data/GUI/OnscreenDebugger/PipelineLogoText.png", x=114,
            y=45, parent=self._fullscreen_node)
        self._topbar = DirectFrame(parent=self._fullscreen_node,
                                   frameSize=(5000, 0, 0, -22),
                                   pos=(0, 0, 0),
                                   frameColor=(0.058, 0.058, 0.058, 1))
        # Hide the logo text in the beginning
        self._pipeline_logo_text.set_pos(150, -150)
        self._topbar.hide()

    def _create_debugger(self):
        """ Creates the debugger contents """

        self._debugger_node = self._fullscreen_node.attach_new_node("DebuggerNode")
        self._debugger_node.set_x(-self._debugger_width)
        self._debugger_bg = DirectFrame(parent=self._debugger_node,
                                        frameSize=(self._debugger_width, 0, 0,
                                                   -2000),
                                        pos=(0, 0, 0),
                                        frameColor=(0.09, 0.09, 0.09, 1))
        self._debugger_bg_bottom = DirectFrame(parent=self._fullscreen_node,
                                               frameSize=(self._debugger_width,
                                                          0, 0, -1),
                                               pos=(0, 0, 1),
                                               frameColor=(0.058, 0.058, 0.058, 1))

        self._create_debugger_content()

    def _create_debugger_content(self):
        """ Internal method to create the content of the debugger """

        debugger_content = self._debugger_node.attach_new_node("DebuggerContent")
        debugger_content.set_z(-160)
        debugger_content.set_x(30)
        BetterOnscreenText(parent=debugger_content, text="Render Mode:", x=0,
            y=0, size=20, color=Vec3(0.9))


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
                    self._debugger_node.posInterval(
                        0.12, Vec3(-self._debugger_width, 0, 0),
                        Vec3(0, 0, 0), blendType="easeInOut"),
                    self._pipeline_logo_text.pos_interval(
                        0.16,
                        self._pipeline_logo_text.get_initial_pos() + Vec3(0, 0, 150),
                        self._pipeline_logo_text.get_initial_pos, blendType="easeInOut"),
                    self._pipeline_logo.hpr_interval(
                        0.12, Vec3(0, 0, 0), Vec3(0, 0, 90), blendType="easeInOut"),
                    self._debugger_bg_bottom.scaleInterval(
                        0.12, Vec3(1, 1, 1), Vec3(1, 1, 110), blendType="easeInOut")
                ))
        else:
            # Show debugger
            self._debugger_interval = Sequence(
                Parallel(
                    self._pipeline_logo.hpr_interval(
                        0.12, Vec3(0, 0, 90), Vec3(0, 0, 0), blendType="easeInOut"),
                    self._pipeline_logo_text.pos_interval(
                        0.12, self._pipeline_logo_text.get_initial_pos(),
                        self._pipeline_logo_text.get_initial_pos() + Vec3(0, 0, 150),
                        blendType="easeInOut"),
                    self._debugger_node.posInterval(
                        0.12, Vec3(0, 0, 0), Vec3(-self._debugger_width, 0),
                        blendType="easeInOut"),
                    self._debugger_bg_bottom.scaleInterval(
                        0.12, Vec3(1, 1, 110), Vec3(1, 1, 1), blendType="easeInOut")
                ))
        self._debugger_interval.start()
        self._debugger_visible = not self._debugger_visible
