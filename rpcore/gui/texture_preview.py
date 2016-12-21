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

from panda3d.core import Vec3, SamplerState, PNMImage

from rpcore.globals import Globals
from rpcore.image import Image
from rpcore.gui.draggable_window import DraggableWindow
from rpcore.gui.sprite import Sprite
from rpcore.gui.text import Text
from rpcore.gui.button import Button
from rpcore.gui.slider import Slider
from rpcore.gui.labeled_checkbox import LabeledCheckbox

from rpcore.util.display_shader_builder import DisplayShaderBuilder


class TexturePreview(DraggableWindow):

    """ Small window which provides a preview of a texture """

    def __init__(self, pipeline, parent):
        DraggableWindow.__init__(self, width=1600, height=900, parent=parent,
                                 title="Texture Viewer")
        self._pipeline = pipeline
        self._current_tex = None
        self._mip_slider = None
        self._mip_text = None
        self._slice_slider = None
        self._slice_text = None
        self._preview_image = None
        self._create_components()

    def _find_dimensions(self, tex):
        """ Determines the dimensions to show the texture at """
        w, h = tex.get_x_size(), tex.get_y_size()
        if h > 1 and w > 0:
            scale_x = (self._width - 40.0) / w
            scale_y = (self._height - 110.0) / h
            scale_f = min(scale_x, scale_y)
            if scale_f >= 1.0:
                # Make sure we choose a fitting scale factor to avoid
                # crushing pixels
                # scale_f = int(scale_f)
                pass
            display_w = int(scale_f * w)
            display_h = int(scale_f * h)
            return display_w, display_h
        else:
            display_w = self._width - 40
            display_h = self._height - 110
            return display_w, display_h

    def present(self, tex):
        """ "Presents" a given texture and shows the window """
        self._current_tex = tex
        self.set_title(tex.get_name())
        self._content_node.node().remove_all_children()

        display_w, display_h = self._find_dimensions(tex)

        image = Sprite(
            image=tex, parent=self._content_node, x=20, y=90, w=display_w,
            h=display_h, any_filter=False, transparent=False)
        self._make_description(tex)
        estimated_bytes = tex.estimate_texture_memory()
        size_desc = "Estimated memory: {:2.2f} MB".format(
            estimated_bytes / (1024.0 ** 2))

        Text(text=size_desc, parent=self._content_node, x=self._width - 20.0,
             y=70, size=18, color=Vec3(0.34, 0.564, 0.192), align="right")

        self._header_offset = len(size_desc) * 9 + 140

        if tex.uses_mipmaps():
            self._make_mipmap_slider(tex)

        if tex.get_z_size() > 1:
            self._make_z_slider(tex)

        self._make_luminance_slider()
        self._make_tonemapping_options()

        self._btn_export = Button(
            parent=self._content_node, x=self._header_offset, y=58, text="Export",
            width=120, callback=self._export_image, bg=(0.34, 0.564, 0.192, 1))

        self._header_offset += 120 + 30
        self._prepare_inputs(tex, image, display_w, display_h)
        self._preview_image = image
        self.show()

    def _make_description(self, tex):
        description = ""
        description += "{:d} x {:d} x {:d}".format(
            tex.get_x_size(), tex.get_y_size(), tex.get_z_size())
        description += ", {:s}, {:s}".format(
            Image.format_format(tex.get_format()).upper(),
            Image.format_component_type(tex.get_component_type()).upper())
        Text(text=description, parent=self._content_node, x=17, y=70,
             size=16, color=Vec3(0.6, 0.6, 0.6))

    def _prepare_inputs(self, tex, image, display_w, display_h):
        image.set_shader_input("slice", 0)
        image.set_shader_input("mipmap", 0)
        image.set_shader_input("brightness", 1)
        image.set_shader_input("tonemap", False)

        stage_sampler = SamplerState()
        stage_sampler.set_minfilter(SamplerState.FT_nearest)
        stage_sampler.set_magfilter(SamplerState.FT_nearest)
        stage_sampler.set_wrap_u(SamplerState.WM_clamp)
        stage_sampler.set_wrap_v(SamplerState.WM_clamp)
        stage_sampler.set_wrap_w(SamplerState.WM_clamp)

        preview_shader = DisplayShaderBuilder.build(tex, display_w, display_h)
        image.set_shader(preview_shader)
        image.set_shader_input("DisplayTex", tex, stage_sampler)

    def _make_mipmap_slider(self, tex):
        max_mips = tex.get_expected_num_mipmap_levels() - 1
        self._mip_slider = Slider(
            parent=self._content_node, size=140, min_value=0, max_value=max_mips,
            callback=self._set_mip, x=self._header_offset, y=65, value=0)
        self._header_offset += 140 + 5

        self._mip_text = Text(
            text="MIP: 5", parent=self._content_node, x=self._header_offset, y=72, size=18,
            color=Vec3(1, 0.4, 0.4), may_change=1)
        self._header_offset += 50 + 30

    def _make_z_slider(self, tex):
        self._slice_slider = Slider(
                parent=self._content_node, size=250, min_value=0,
                max_value=tex.get_z_size() - 1, callback=self._set_slice, x=self._header_offset,
                y=65, value=0)
        self._header_offset += 250 + 5

        self._slice_text = Text(
            text="Z: 5", parent=self._content_node, x=self._header_offset, y=72, size=18,
            color=Vec3(0.4, 1, 0.4), may_change=1)

        self._header_offset += 50 + 30

    def _make_luminance_slider(self):
        self._luminance_slider = Slider(
            parent=self._content_node, size=140, min_value=-14, max_value=14,
            callback=self._set_brightness, x=self._header_offset, y=65, value=0)
        self._header_offset += 140 + 5
        self._bright_text = Text(
            text="Bright: 1", parent=self._content_node, x=self._header_offset, y=72, size=18,
            color=Vec3(0.4, 0.4, 1), may_change=1)
        self._header_offset += 100 + 30

    def _make_tonemapping_options(self):
        self._tonemap_box = LabeledCheckbox(
            parent=self._content_node, x=self._header_offset, y=58, text="Tonemap",
            text_color=Vec3(1, 0.4, 0.4), chb_checked=False,
            chb_callback=self._set_enable_tonemap,
            text_size=18, expand_width=90)
        self._header_offset += 90 + 50


    def _set_slice(self):
        idx = int(self._slice_slider.value)
        self._preview_image.set_shader_input("slice", idx)
        self._slice_text.set_text("Z: " + str(idx))

    def _set_mip(self):
        idx = int(self._mip_slider.value)
        self._preview_image.set_shader_input("mipmap", idx)
        self._mip_text.set_text("MIP " + str(idx))

    def _set_brightness(self):
        val = self._luminance_slider.value
        scale = 2 ** val
        self._bright_text.set_text("Bright: " + str(round(scale, 3)))
        self._preview_image.set_shader_input("brightness", scale)

    def _set_enable_tonemap(self, enable_tonemap):
        self._preview_image.set_shader_input("tonemap", enable_tonemap)

    def _create_components(self):
        """ Internal method to init the components """
        DraggableWindow._create_components(self)
        self._content_node = self._node.attach_new_node("content")

    def _export_image(self, event):  # pylint: disable=unused-argument
        """ Exports the image to disk, and also writes a csv file containing
        the pixel values, in case the texture contains integer data """
        self.debug("Exporting image")
        Globals.base.graphics_engine.extract_texture_data(
            self._current_tex, Globals.base.win.get_gsg())

        name = self._current_tex.get_name()
        name = name.replace(" ", "_").replace(":", "_")
        self._current_tex.write(name + ".png")

        comp = self._current_tex.get_component_type()
        if comp in [Image.T_int, Image.T_unsigned_short, Image.T_short, Image.T_unsigned_int]:
            self.debug("Exporting csv")

            img = PNMImage(self._current_tex.get_x_size(),
                           self._current_tex.get_y_size(), 1, 2**16 - 1)

            self._current_tex.store(img)

            output_lines = []
            for y in range(self._current_tex.get_y_size()):
                line = []
                for x in range(self._current_tex.get_x_size()):
                    line.append(img.get_gray_val(x, y))
                output_lines.append(line)

            with open(name + ".csv", "w") as handle:
                for line in output_lines:
                    handle.write(";".join([str(i) for i in line]) + "\n")

        self.debug("Done.")
