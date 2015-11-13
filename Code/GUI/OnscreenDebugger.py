

from panda3d.core import Vec3, Vec2, RenderState, TransformState
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectOptionMenu import DirectOptionMenu
from direct.gui.DirectGuiBase import DGG
from direct.interval.IntervalGlobal import Parallel, Sequence


from .BetterOnscreenImage import BetterOnscreenImage
from .BufferViewer import BufferViewer
from .PipeViewer import PipeViewer
from .BetterOnscreenText import BetterOnscreenText
from .BetterLabeledCheckbox import BetterLabeledCheckbox
from .CheckboxCollection import CheckboxCollection
from .FastText import FastText
from .ErrorMessageDisplay import ErrorMessageDisplay

from ..Util.DebugObject import DebugObject
from ..Globals import Globals
from functools import partial


class OnscreenDebugger(DebugObject):

    """ This class manages the onscreen gui """

    def __init__(self, pipeline):
        DebugObject.__init__(self)
        self.debug("Creating debugger")
        self._pipeline = pipeline

        self._fullscreen_node = Globals.base.pixel2d.attach_new_node(
            "PipelineDebugger")
        self._create_components()
        self._init_keybindings()
        self._init_notify()

    def _create_components(self):
        """ Creates the gui components """

        # When using small resolutions, scale the GUI so its still useable,
        # otherwise the sub-windows are bigger than the main window
        scale_factor = min(1.0, Globals.base.win.get_x_size() / 1800.0)
        # scale_factor = 1.0
        self._fullscreen_node.set_scale(scale_factor)

        # Component values
        self._debugger_width = 460

        # Create states
        self._debugger_visible = False

        # Create intervals
        self._debugger_interval = None

        # Create the actual GUI
        self._create_debugger()
        self._create_topbar()
        self._create_stats()
        self._buffer_viewer = BufferViewer(self._pipeline, self._fullscreen_node)
        self._pipe_viewer = PipeViewer(self._pipeline, self._fullscreen_node)

    def _init_notify(self):
        """ Inits the notify stream which gets all output from panda and parses
        it """
        self._error_msg_handler = ErrorMessageDisplay()

    def update(self):
        """ Updates the gui """
        self._update_stats()
        self._error_msg_handler.update()    

    def _create_topbar(self):
        """ Creates the topbar """
        self._pipeline_logo = BetterOnscreenImage(
            image="Data/GUI/OnscreenDebugger/PipelineLogo.png", x=30, y=30,
            parent=self._fullscreen_node)
        self._pipeline_logo_text = BetterOnscreenImage(
            image="Data/GUI/OnscreenDebugger/PipelineLogoText.png", x=124,
            y=55, parent=self._fullscreen_node)
        self._topbar = DirectFrame(parent=self._fullscreen_node,
                                   frameSize=(5000, 0, 0, -22),
                                   pos=(0, 0, 0),
                                   frameColor=(0.058, 0.058, 0.058, 1))
        # Hide the logo text in the beginning
        self._pipeline_logo_text.set_pos(150, -150)
        self._topbar.hide()

    def _create_stats(self):
        """ Creates the stats overlay """

        self._overlay_node = Globals.base.aspect2d.attach_new_node("Overlay")
        self._overlay_node.set_pos(Globals.base.getAspectRatio() - 0.07, 1, 1.0 - 0.07)

        self._debug_lines = []

        for i in range(2):
            self._debug_lines.append(FastText(pos=Vec2(0, -i * 0.05),
                parent=self._overlay_node, pixel_size=18, align="right"))

    def _update_stats(self):
        """ Updates the stats overlay """

        clock = Globals.clock
        self._debug_lines[0].set_text("{:3.0f} fps  |  {:3.1f} ms  |  {:3.1f} ms max".format( 
            clock.get_average_frame_rate(),
            1000.0 / max(0.001, clock.get_average_frame_rate()),
            clock.get_max_frame_duration() * 1000.0))
        self._debug_lines[1].set_text(
            "{:4d} render states  |  {:4d} transform states  |  {:4d} commands  |  {:6d} lights".format(
                RenderState.get_num_states(), TransformState.get_num_states(),
                self._pipeline._light_mgr._cmd_queue.get_num_queued_commands(),
                self._pipeline._light_mgr._light_storage.get_num_stored_lights()))

        for line in self._debug_lines:
            line.update()

    def _create_debugger(self):
        """ Creates the debugger contents """

        debugger_opacity = 0.9

        self._debugger_node = self._fullscreen_node.attach_new_node("DebuggerNode")
        self._debugger_node.set_x(-self._debugger_width)
        self._debugger_bg = DirectFrame(parent=self._debugger_node,
                                        frameSize=(self._debugger_width, 0, -127,
                                                   -1020),
                                        pos=(0, 0, 0),
                                        frameColor=(0.09, 0.09, 0.09, debugger_opacity))
        self._debugger_bg_bottom = DirectFrame(parent=self._fullscreen_node,
                                               frameSize=(self._debugger_width,
                                                          0, 0, -1),
                                               pos=(0, 0, 1),
                                               frameColor=(0.09, 0.09, 0.09, 0*debugger_opacity))
        self._debugger_divider = DirectFrame(parent=self._debugger_node,
                                               frameSize=(self._debugger_width,
                                                          0, 0, -3),
                                               pos=(0, 0, -125),
                                               frameColor=(0.15, 0.15, 0.15, 0*debugger_opacity))

        self._create_debugger_content()

    def _create_debugger_content(self):
        """ Internal method to create the content of the debugger """

        debugger_content = self._debugger_node.attach_new_node("DebuggerContent")
        debugger_content.set_z(-190)
        debugger_content.set_x(40)
        heading_color = Vec3(0.7, 0.7, 0.24) * 1.2
        BetterOnscreenText(parent=debugger_content, text="Render Mode:", x=0,
            y=0, size=20, color=heading_color)

        render_modes = [
            ("Default", ""),
            ("Metallic", "METALLIC"),
            ("BaseColor", "BASECOLOR"),
            ("Roughness", "ROUGHNESS"),
            ("Specular", "SPECULAR"),
            ("Normal", "NORMAL"),
            # ("Velocity", "VELOCITY")
            # ("Occlusion",
            # "Lighting",
            # "Raw-Lighting",
            # "Scattering",
            # "GI-Diffuse",
            # "GI-Specular",
            # "Ambient",
            # "PSSM-Splits",
            # "Shadowing",
            # "Bloom"
        ]


        row_width = 200
        collection = CheckboxCollection()

        for idx, (mode, mode_id) in enumerate(render_modes):
            offs_y = (idx // 2) * 37 + 40
            offs_x = (idx % 2) * row_width
            box = BetterLabeledCheckbox(parent=debugger_content, x=offs_x,
                y=offs_y, text=mode, text_color=Vec3(0.9), radio=True,
                chb_checked=(mode == "Default"), text_size=17, expand_width=160,
                chb_callback=partial(self._set_render_mode, mode_id))
            collection.add(box.get_checkbox())

        """
        offs_top = 150 + (len(render_modes) // 2) * 37
        features = [
            "Occlusion",
            "Upscale Blur",
            "Scattering",
            "Global Illumination",
            "Ambient",
            "Motion Blur",
            "Anti-Aliasing",
            "Shadows",
            "Correct color",
            "PCSS",
            "PCF",
            "Env. Filtering",
            "PB Shading",
            "Bloom",
            "Diffuse AA"
        ]

        BetterOnscreenText(parent=debugger_content, text="Feature selection:", x=0,
            y=offs_top, size=20, color=heading_color)

        for idx, feature in enumerate(features):
            offs_y = (idx // 2) * 37 + 40 + offs_top
            offs_x = (idx % 2) * row_width
            box = BetterLabeledCheckbox(parent=debugger_content, x=offs_x,
                y=offs_y, text=feature, text_color=Vec3(0.9), radio=False,
                chb_checked=True, text_size=17, expand_width=160)
        """

    def _set_render_mode(self, mode_id, value):
        """ Callback which gets called when a render mode got selected """
        if not value:
            return
        
        # Clear old defines
        self._pipeline.get_stage_mgr().remove_define_if(lambda name: name.startswith("_RM__"))

        # print("Setting render mode: ", mode_id)
        if mode_id == "":
            self._pipeline.get_stage_mgr().define("ANY_DEBUG_MODE", 0)
        else:
            self._pipeline.get_stage_mgr().define("ANY_DEBUG_MODE", 1)
            self._pipeline.get_stage_mgr().define("_RM__" + mode_id, 1)

        # Reload all shaders
        self._pipeline.reload_shaders()

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
                        Vec3(40, 0, 0), blendType="easeInOut"),
                    self._pipeline_logo_text.pos_interval(
                        0.16,
                        self._pipeline_logo_text.get_initial_pos() + Vec3(0, 0, 150),
                        self._pipeline_logo_text.get_initial_pos, blendType="easeInOut"),
                    self._pipeline_logo.hpr_interval(
                        0.12, Vec3(0, 0, 0), Vec3(0, 0, 90), blendType="easeInOut"),
                    self._debugger_bg_bottom.scaleInterval(
                        0.12, Vec3(1, 1, 1), Vec3(1, 1, 126), blendType="easeInOut")
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
                        0.12, Vec3(40, 0, 0), Vec3(-self._debugger_width, 0),
                        blendType="easeInOut"),
                    self._debugger_bg_bottom.scaleInterval(
                        0.12, Vec3(1, 1, 126), Vec3(1, 1, 1), blendType="easeInOut")
                ))
        self._debugger_interval.start()
        self._debugger_visible = not self._debugger_visible
