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

from panda3d.core import Vec3, Texture

from .draggable_window import DraggableWindow
from .sprite import Sprite
from .text import Text
from .slider import Slider

from ..util.display_shader_builder import DisplayShaderBuilder

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

    def present(self, tex):
        """ "Presents" a given texture and shows the window """
        self._current_tex = tex

        self.set_title(tex.get_name())

        # Remove old content
        self._content_node.node().remove_all_children()

        w, h = tex.get_x_size(), tex.get_y_size()
        if h > 1:
            scale_x = (self._width - 40.0) / w
            scale_y = (self._height - 110.0) / h
            scale_f = min(scale_x, scale_y)
            display_w = scale_f * w
            display_h = scale_f * h

        else:
            display_w = self._width - 40
            display_h = self._height - 110

        image = Sprite(
            image=tex, parent=self._content_node, x=20, y=90, w=display_w,
            h=display_h, any_filter=False, transparent=False)
        description = ""

        # Image size
        description += "{:d} x {:d} x {:d}".format(
            tex.get_x_size(), tex.get_y_size(), tex.get_z_size())

        # Image type
        description += ", {:s}, {:s}".format(
            Texture.format_format(tex.get_format()).upper(),
            Texture.format_component_type(tex.get_component_type()).upper())

        Text(text=description, parent=self._content_node, x=20, y=70,
             size=18, color=Vec3(0.6, 0.6, 0.6))

        estimated_bytes = tex.estimate_texture_memory()
        size_desc = "Estimated memory: {:2.2f} MB".format(
            estimated_bytes / (1024.0 ** 2))

        Text(text=size_desc, parent=self._content_node, x=self._width - 20.0,
             y=70, size=18, color=Vec3(0.34, 0.564, 0.192), align="right")

        if tex.uses_mipmaps():
            # Create mip slider
            max_mips = tex.get_expected_num_mipmap_levels() - 1
            self._mip_slider = Slider(
                parent=self._content_node, size=200, min_value=0, max_value=max_mips,
                callback=self._set_mip, x=850, y=63, value=0)
            self._mip_text = Text(
                text="Mipmap: 5", parent=self._content_node, x=1080, y=70, size=18,
                color=Vec3(0.6, 0.6, 0.6), may_change=1)

        if tex.get_z_size() > 1:
            self._slice_slider = Slider(
                parent=self._content_node, size=250, min_value=0,
                max_value=tex.get_z_size() - 1, callback=self._set_slice, x=450,
                y=63, value=0)
            self._slice_text = Text(
                text="Slice: 5", parent=self._content_node, x=710, y=70, size=18,
                color=Vec3(0.6, 0.6, 0.6), may_change=1)

        image.set_shader_input("slice", 0)
        image.set_shader_input("mipmap", 0)

        preview_shader = DisplayShaderBuilder.build(tex, display_w, display_h)
        image.set_shader(preview_shader)

        self._preview_image = image
        self.show()

    def _set_slice(self):
        idx = int(self._slice_slider.value)
        self._preview_image.set_shader_input("slice", idx)
        self._slice_text.set_text("Slice: " + str(idx))

    def _set_mip(self):
        idx = int(self._mip_slider.value)
        self._preview_image.set_shader_input("mipmap", idx)
        self._mip_text.set_text("Mipmap: " + str(idx))

    def _create_components(self):
        """ Internal method to init the components """
        DraggableWindow._create_components(self)
        self._content_node = self._node.attach_new_node("content")
