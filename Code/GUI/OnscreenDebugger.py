
from __future__ import division

from functools import partial

from panda3d.core import Vec4, Vec3, Vec2, RenderState, TransformState
from direct.gui.DirectFrame import DirectFrame
from direct.interval.IntervalGlobal import Parallel, Sequence

from .BetterOnscreenImage import BetterOnscreenImage
from .BufferViewer import BufferViewer
from .PipeViewer import PipeViewer
from .BetterOnscreenText import BetterOnscreenText
from .BetterLabeledCheckbox import BetterLabeledCheckbox
from .CheckboxCollection import CheckboxCollection
from .FastTextNode import FastTextNode
from .ErrorMessageDisplay import ErrorMessageDisplay
from .ExposureWidget import ExposureWidget

from ..Util.DebugObject import DebugObject
from ..Globals import Globals
from ..BaseManager import BaseManager

from ..Native import NATIVE_CXX_LOADED
from ..RenderTarget import RenderTarget
from ..Util.Image import Image

class OnscreenDebugger(BaseManager):

    """ This class manages the onscreen gui """

    def __init__(self, pipeline):
        BaseManager.__init__(self)
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
        self._create_hints()

        self._buffer_viewer = BufferViewer(self._pipeline, self._fullscreen_node)
        self._pipe_viewer = PipeViewer(self._pipeline, self._fullscreen_node)

        self._exposure_node = self._fullscreen_node.attach_new_node("ExposureWidget")
        self._exposure_node.set_pos(Globals.base.win.get_x_size() - 200, 1, -Globals.base.win.get_y_size() + 120)
        self._exposure_widget = ExposureWidget(self._pipeline, self._exposure_node)

    def _init_notify(self):
        """ Inits the notify stream which gets all output from panda and parses
        it """
        self._error_msg_handler = ErrorMessageDisplay()

    def do_update(self):
        """ Updates the gui """
        self._update_stats()
        self._error_msg_handler.update()

    def get_error_msg_handler(self):
        """ Returns the error message handler """
        return self._error_msg_handler

    def _create_topbar(self):
        """ Creates the topbar """
        self._pipeline_logo = BetterOnscreenImage(
            image="Data/GUI/OnscreenDebugger/PipelineLogoText.png", x=30, y=30,
            parent=self._fullscreen_node)

    def _create_stats(self):
        """ Creates the stats overlay """
        self._overlay_node = Globals.base.aspect2d.attach_new_node("Overlay")
        self._overlay_node.set_pos(Globals.base.getAspectRatio() - 0.07, 1, 1.0 - 0.07)
        self._debug_lines = []
        for i in range(4):
            self._debug_lines.append(FastTextNode(
                pos=Vec2(0, -i * 0.046), parent=self._overlay_node,
                pixel_size=16, align="right", color=Vec3(1)))

    def _create_hints(self):
        """ Creates the hints like keybindings and when reloading shaders """
        self._hint_reloading = BetterOnscreenImage(
            image="Data/GUI/OnscreenDebugger/ShaderReloadHint.png",
            x= (Globals.base.win.get_x_size() - 465) // 2, y=220,
            parent=Globals.base.pixel2d)
        self.set_reload_hint_visible(False)

        if not NATIVE_CXX_LOADED:
            # Warning when using the python version
            python_warning = BetterOnscreenImage(
                image="Data/GUI/OnscreenDebugger/PythonWarning.png",
                x=(Globals.base.win.get_x_size() - 1054) // 2,
                y=Globals.base.win.get_y_size() - 118 - 40, parent=self._fullscreen_node)

            Sequence(
                python_warning.color_scale_interval(1.0, Vec4(1, 1, 1, 0.8), Vec4(1, 1, 1, 1), blendType="easeInOut"),
                python_warning.color_scale_interval(1.0, Vec4(1, 1, 1, 1.0), Vec4(1, 1, 1, 0.8), blendType="easeInOut"),
            ).loop()

        # Keybinding hints
        self._keybinding_instructions = BetterOnscreenImage(
            image="Data/GUI/OnscreenDebugger/KeyBindings.png", x=30, y=Globals.base.win.get_y_size() - 510,
            parent=self._fullscreen_node, any_filter=False)

    def _update_stats(self):
        """ Updates the stats overlay """
        clock = Globals.clock
        self._debug_lines[0].set_text("{:3.0f} fps  |  {:3.1f} ms  |  {:3.1f} ms max".format(
            clock.get_average_frame_rate(),
            1000.0 / max(0.001, clock.get_average_frame_rate()),
            clock.get_max_frame_duration() * 1000.0))

        text = "{:4d} render states  |  {:4d} transforms"
        text += "  |  {:4d} commands  |  {:6d} lights  |  {:5d} shadow sources"
        self._debug_lines[1].set_text(text.format(
            RenderState.get_num_states(), TransformState.get_num_states(),
            self._pipeline.get_light_mgr().get_cmd_queue().get_num_processed_commands(),
            self._pipeline.get_light_mgr().get_num_lights(),
            self._pipeline.get_light_mgr().get_num_shadow_sources(),
            ))

        text = "{:3.0f} MiB VRAM usage  |  {:5d} images  |  {:5d} textures  |  "
        text += "{:5d} render targets  |  {:3d} plugins"
        tex_info = self._buffer_viewer.get_stage_information()
        self._debug_lines[2].set_text(text.format(
                tex_info["memory"] / (1024**2) ,
                Image._NUM_IMAGES,
                tex_info["count"],
                RenderTarget._NUM_BUFFERS_ALLOCATED,
                self._pipeline.get_plugin_mgr().get_interface().get_active_plugin_count()
            ))

        text = "{} ({:1.3f})  |  {:3d} active constraints"
        self._debug_lines[3].set_text(text.format(
                self._pipeline.get_daytime_mgr().get_time_str(),
                self._pipeline.get_daytime_mgr().get_time(),
                self._pipeline.get_daytime_mgr().get_num_constraints()
            ))

    def _create_debugger(self):
        """ Creates the debugger contents """
        debugger_opacity = 1.0
        self._debugger_node = self._fullscreen_node.attach_new_node("DebuggerNode")
        self._debugger_node.set_pos(30, 0, -Globals.base.win.get_y_size() + 820)
        self._debugger_bg_img = BetterOnscreenImage(
            image="Data/GUI/OnscreenDebugger/DebuggerBackground.png", x=0, y=0,
            parent=self._debugger_node, any_filter=False
        )
        self._create_debugger_content()

    def set_reload_hint_visible(self, flag):
        """ Sets whether the shader reload hint is visible """
        if flag:
            self._hint_reloading.show()
        else:
            self._hint_reloading.hide()

    def _create_debugger_content(self):
        """ Internal method to create the content of the debugger """

        debugger_content = self._debugger_node.attach_new_node("DebuggerContent")
        debugger_content.set_z(-20)
        debugger_content.set_x(20)
        heading_color = Vec3(0.7, 0.7, 0.24) * 1.2

        render_modes = [
            ("Default", "",                     False, ""),
            ("Diffuse", "DIFFUSE",              False, ""),
            ("Roughness", "ROUGHNESS",          False, ""),
            ("Specular", "SPECULAR",            False, ""),
            ("Normal", "NORMAL",                False, ""),
            ("Metallic", "METALLIC",            False, ""),
            ("Translucency", "TRANSLUCENCY",    False, ""),
            ("PSSM Splits", "PSSM_SPLITS",      True , "PSSM"),
            ("Ambient Occlusion", "OCCLUSION",  False, "AO")
        ]

        row_width = 200
        collection = CheckboxCollection()

        for idx, (mode, mode_id, requires_cxx, requires_plugin) in enumerate(render_modes):
            offs_y = idx * 24 + 45
            offs_x = 0
            enabled = True
            if requires_cxx and not NATIVE_CXX_LOADED:
                enabled = False

            if requires_plugin:
                if not self._pipeline.get_plugin_mgr().get_interface().is_plugin_enabled(requires_plugin):
                    enabled = False

            box = BetterLabeledCheckbox(
                parent=debugger_content, x=offs_x, y=offs_y, text=mode.upper(),
                text_color=Vec3(0.4), radio=True, chb_checked=(mode == "Default"),
                chb_callback=partial(self._set_render_mode, mode_id),
                text_size=14, expand_width=230, enabled=enabled)
            collection.add(box.get_checkbox())

    def _set_render_mode(self, mode_id, value):
        """ Callback which gets called when a render mode got selected """
        if not value:
            return

        # Clear old defines
        self._pipeline.get_stage_mgr().remove_define_if(lambda name: name.startswith("_RM__"))

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
        Globals.base.accept("f5", self._toggle_gui_visible)

    def _toggle_gui_visible(self):
        """ Shows / Hides the gui """
        if not Globals.base.pixel2d.is_hidden():
            Globals.base.pixel2d.hide()
            Globals.base.aspect2d.hide()
            Globals.base.render2d.hide()
        else:
            Globals.base.pixel2d.show()
            Globals.base.aspect2d.show()
            Globals.base.render2d.show()
        
    def _toggle_debugger(self):
        """ Internal method to hide or show the debugger """
        # TODO
        return
