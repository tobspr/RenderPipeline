"""

RenderPipeline

Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

from __future__ import division
from functools import partial
from rplibs.six.moves import range

from panda3d.core import Vec4, Vec3, Vec2, RenderState, TransformState
from direct.interval.IntervalGlobal import Sequence

from rplibs.yaml import load_yaml_file

from rpcore.gui.sprite import Sprite
from rpcore.gui.buffer_viewer import BufferViewer
from rpcore.gui.pipe_viewer import PipeViewer
from rpcore.gui.labeled_checkbox import LabeledCheckbox
from rpcore.gui.checkbox_collection import CheckboxCollection
from rpcore.gui.text_node import TextNode
from rpcore.gui.error_message_display import ErrorMessageDisplay
from rpcore.gui.exposure_widget import ExposureWidget
from rpcore.gui.pixel_inspector import PixelInspector

from rpcore.globals import Globals
from rpcore.base_manager import BaseManager

from rpcore.native import NATIVE_CXX_LOADED
from rpcore.render_target import RenderTarget
from rpcore.image import Image

class Debugger(BaseManager):

    """ This class manages the onscreen gui and """

    def __init__(self, pipeline):
        BaseManager.__init__(self)
        self.debug("Creating debugger")
        self._pipeline = pipeline

        self._load_config()
        self._fullscreen_node = Globals.base.pixel2d.attach_new_node(
            "PipelineDebugger")
        self._create_components()
        self._init_keybindings()
        self._init_notify()

    def _load_config(self):
        """ Loads the gui configuration from config/debugging.yaml """
        self._config = load_yaml_file("$$config/debugging.yaml")

    def _create_components(self):
        """ Creates the gui components """

        # When using small resolutions, scale the GUI so its still useable,
        # otherwise the sub-windows are bigger than the main window
        scale_factor = min(1.0, Globals.base.win.get_x_size() / 1920.0)
        self._fullscreen_node.set_scale(scale_factor)
        self._gui_scale = scale_factor

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
        self._exposure_node.set_pos(
            Globals.base.win.get_x_size() / self._gui_scale - 200,
            1, -Globals.base.win.get_y_size() / self._gui_scale + 120)
        self._exposure_widget = ExposureWidget(self._pipeline, self._exposure_node)
        self._pixel_widget = PixelInspector(self._pipeline)

    def _init_notify(self):
        """ Inits the notify stream which gets all output from panda and parses
        it """
        self._error_msg_handler = ErrorMessageDisplay()

    def do_update(self):
        """ Updates the gui """
        self._update_stats()
        self._error_msg_handler.update()
        self._pixel_widget.update()


    def get_error_msg_handler(self):
        """ Returns the error message handler """
        return self._error_msg_handler

    def _create_topbar(self):
        """ Creates the topbar """
        self._pipeline_logo = Sprite(
            image="data/gui/pipeline_logo_text.png", x=30, y=30,
            parent=self._fullscreen_node)

    def _create_stats(self):
        """ Creates the stats overlay """
        self._overlay_node = Globals.base.aspect2d.attach_new_node("Overlay")
        self._overlay_node.set_pos(Globals.base.get_aspect_ratio() - 0.07, 1, 1.0 - 0.07)
        self._debug_lines = []
        for i in range(4):
            self._debug_lines.append(TextNode(
                pos=Vec2(0, -i * 0.046), parent=self._overlay_node,
                pixel_size=16, align="right", color=Vec3(1)))

    def _create_hints(self):
        """ Creates the hints like keybindings and when reloading shaders """
        self._hint_reloading = Sprite(
            image="data/gui/shader_reload_hint.png",
            x=float((Globals.base.win.get_x_size()) // 2) / self._gui_scale - 465 // 2, y=220,
            parent=self._fullscreen_node)
        self.set_reload_hint_visible(False)

        if not NATIVE_CXX_LOADED:
            # Warning when using the python version
            python_warning = Sprite(
                image="data/gui/python_warning.png",
                x=((Globals.base.win.get_x_size()/self._gui_scale) - 1054) // 2,
                y=(Globals.base.win.get_y_size()/self._gui_scale) - 118 - 40,
                parent=self._fullscreen_node)

            Sequence(
                python_warning.color_scale_interval(0.7, Vec4(0.3, 1, 1, 0.7), blendType="easeOut"),
                python_warning.color_scale_interval(0.7, Vec4(1, 1, 1, 1.0), blendType="easeOut"),
            ).loop()

        # Keybinding hints
        self._keybinding_instructions = Sprite(
            image="data/gui/keybindings.png", x=30,
            y=Globals.base.win.get_y_size()//self._gui_scale - 510.0,
            parent=self._fullscreen_node, any_filter=False)

    def _update_stats(self):
        """ Updates the stats overlay """
        clock = Globals.clock
        self._debug_lines[0].text = "{:3.0f} fps  |  {:3.1f} ms  |  {:3.1f} ms max".format(
            clock.get_average_frame_rate(),
            1000.0 / max(0.001, clock.get_average_frame_rate()),
            clock.get_max_frame_duration() * 1000.0)

        text = "{:4d} render states  |  {:4d} transforms"
        text += "  |  {:4d} commands  |  {:6d} lights  |  {:5d} shadow sources"
        self._debug_lines[1].text = text.format(
            RenderState.get_num_states(), TransformState.get_num_states(),
            self._pipeline.light_mgr.get_cmd_queue().num_processed_commands,
            self._pipeline.light_mgr.get_num_lights(),
            self._pipeline.light_mgr.get_num_shadow_sources())

        text = "{:3.0f} MiB VRAM usage  |  {:5d} images  |  {:5d} textures  |  "
        text += "{:5d} render targets  |  {:3d} plugins"
        tex_info = self._buffer_viewer.stage_information
        self._debug_lines[2].text = text.format(
            tex_info["memory"] / (1024**2),
            Image.get_image_count(),
            tex_info["count"],
            RenderTarget.get_num_buffers(),
            len(self._pipeline.plugin_mgr.enabled_plugins))

        text = "{} ({:1.3f})  |  {:3d} daytime settings  |  X {:3.1f}  Y {:3.1f}  Z {:3.1f}"
        self._debug_lines[3].text = text.format(
            self._pipeline.daytime_mgr.formatted_time,
            self._pipeline.daytime_mgr.time,
            self._pipeline.plugin_mgr.num_day_settings,
            Globals.base.camera.get_x(Globals.base.render),
            Globals.base.camera.get_y(Globals.base.render),
            Globals.base.camera.get_z(Globals.base.render),)

    def _create_debugger(self):
        """ Creates the debugger contents """
        self._debugger_node = self._fullscreen_node.attach_new_node("DebuggerNode")
        self._debugger_node.set_pos(30, 0, -Globals.base.win.get_y_size()//self._gui_scale + 820.0)
        self._debugger_bg_img = Sprite(
            image="data/gui/debugger_background.png", x=0, y=0,
            parent=self._debugger_node, any_filter=False)
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

        render_modes = [("Default", "", False, "")]

        # Read modes from configuration
        for mode in self._config["render_modes"]:
            data = [mode["name"], mode["key"]]
            data.append("cxx_only" in mode and mode["cxx_only"])
            data.append(mode["requires"] if "requires" in mode else "")
            render_modes.append(data)

        collection = CheckboxCollection()

        for idx, (mode, mode_id, requires_cxx, requires_plugin) in enumerate(render_modes):
            offs_y = idx * 24 + 45
            offs_x = 0
            enabled = True
            if requires_cxx and not NATIVE_CXX_LOADED:
                enabled = False

            if requires_plugin:
                if not self._pipeline.plugin_mgr.is_plugin_enabled(requires_plugin):
                    enabled = False

            box = LabeledCheckbox(
                parent=debugger_content, x=offs_x, y=offs_y, text=mode.upper(),
                text_color=Vec3(0.4), radio=True, chb_checked=(mode == "Default"),
                chb_callback=partial(self._set_render_mode, mode_id),
                text_size=14, expand_width=230, enabled=enabled)
            collection.add(box.checkbox)

    def _set_render_mode(self, mode_id, value):
        """ Callback which gets called when a render mode got selected """
        if not value:
            return

        # Clear old defines
        self._pipeline.stage_mgr.remove_define_if(lambda name: name.startswith("_RM__"))

        if mode_id == "":
            self._pipeline.stage_mgr.define("ANY_DEBUG_MODE", 0)
        else:
            self._pipeline.stage_mgr.define("ANY_DEBUG_MODE", 1)
            self._pipeline.stage_mgr.define("_RM__" + mode_id, 1)

        # Reload all shaders
        self._pipeline.reload_shaders()

    def _init_keybindings(self):
        """ Inits the debugger keybindings """
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
