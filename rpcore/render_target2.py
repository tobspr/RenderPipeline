"""

RenderTarget

Copyright (c) 2015 tobspr <tobias.springer1@gmail.com>

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

from __future__ import print_function, division

from panda3d.core import GraphicsOutput, CardMaker, OmniBoundingVolume, Texture
from panda3d.core import AuxBitplaneAttrib, NodePath, OrthographicLens, Geom
from panda3d.core import Camera, Vec4, TransparencyAttrib, StencilAttrib
from panda3d.core import ColorWriteAttrib, DepthWriteAttrib, GeomVertexData
from panda3d.core import WindowProperties, FrameBufferProperties, GraphicsPipe
from panda3d.core import GeomVertexFormat, GeomNode, GeomVertexWriter
from panda3d.core import GeomTriangles, SamplerState, LVecBase2i, DepthTestAttrib

from rplibs.six.moves import range
from rplibs.six import iterkeys, itervalues, iteritems

from rpcore.render_target import RenderTarget
from rpcore.gui.buffer_viewer import BufferViewer
from rpcore.globals import Globals
from rpcore.rp_object import RPObject

class setter(object):
    """ Setter only property """
    def __init__(self, func):
        self.__func = func
        self.__doc__ = func.__doc__

    def __set__(self, name, value):
        return self.__func(name, value)

class RenderTarget2(RPObject):

    """ Second version of the RenderTarget, IN DEVELOPMENT! The pipeline is
    slowly updated to use this version of the render target, when the process
    is done this will replace the first version. """

    _NUM_BUFFERS_ALLOCATED = 0

    def __init__(self, name="target"):
        RPObject.__init__(self, "RT-" + name)
        self._targets = {}
        self._color_bits = (0, 0, 0, 0)
        self._aux_bits = 8
        self._aux_count = 0
        self._depth_bits = 0
        self._size = LVecBase2i(-1, -1)
        self._source_camera = Globals.base.cam
        self._source_window = Globals.base.win
        self._source_region = self._find_main_region()
        self._active = False
        self._internal_buffer = None
        self._camera = None
        self._node = None
        self._quad = None

        # Public attributes
        self.engine = Globals.base.graphicsEngine
        self.support_transparency = False
        self.use_oversized_triangle = True
        self.create_overlay_quad = True

    #
    # METHODS TO SETUP
    #

    def add_color_attachment(self, bits=8, alpha=False):
        if isinstance(bits, (list, tuple)):
            self._color_bits = (bits[0], bits[1], bits[2], bits[3] if len(bits) == 4 else 0)
        else:
            self._color_bits = ((bits, bits, bits, (bits if alpha else 0)))
        self._targets["color"] = Texture(self.debug_name + "_color")

    def add_depth_attachment(self, bits=32):
        self._depth_bits = 32
        self._targets["depth"] = Texture(self.debug_name + "_depth")

    def add_aux_attachment(self, bits=8):
        self._aux_bits = bits
        self._aux_count += 1

    def add_aux_attachments(self, bits=8, count=1):
        self._aux_bits = bits
        self._aux_count += count

    @setter
    def size(self, *args):
        self._size = LVecBase2i(*args)

    def set_source(self, source_cam, source_win, region=None):
        self._source_camera = source_cam
        self._source_window = source_win
        self._source_region = region


    #
    # METHODS TO QUERY AFTER SETUP
    #


    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, val):
        if self._active is not active:
            self._internal_buffer.get_display_region(0).set_active(active)
            self._active = active
            # self._region.set_active(active)

    @property
    def color_tex(self):
        return self._targets["color"]

    @property
    def depth_tex(self):
        return self._targets["depth"]

    @property
    def aux_tex(self):
        (i for i in sorted(iterkeys(self._targets)) if i.startswith("aux"))

    @property
    def node(self):
        return self._node

    def set_shader_input(self, *args):
        self._node.set_shader_input(*args)

    def set_attrib(self, *args):
        self._node.set_attrib(*args)

    @setter
    def shader(self, shader_obj):
        self._node.set_shader(shader_obj)

    @property
    def internal_buffer(self):
        return self._internal_buffer

    @property
    def targets(self):
        return self._targets

    @property
    def region(self):
        return self._source_region

    @property
    def quad(self):
        return self._quad

    @property
    def camera(self):
        return self._camera

    def prepare_scene_render(self):
        self._create_buffer()

    def prepare_buffer(self):
        self._create_buffer()

        self._node = NodePath("RTRoot")
        self._quad = self._make_fullscreen_quad()
        self._quad.reparent_to(self._node)

        # Prepare fullscreen camera
        buffer_cam = self._make_fullscreen_cam()
        self._camera = self._node.attach_new_node(buffer_cam)

        # Prepare initial state
        initial_state = NodePath("state")
        if self._color_bits.count(0) == 4:
            initial_state.set_attrib(ColorWriteAttrib.make(ColorWriteAttrib.C_off), 1000)
        initial_state.set_attrib(
            DepthWriteAttrib.make(DepthWriteAttrib.M_none), 1000)
        initial_state.set_attrib(
            DepthTestAttrib.make(DepthTestAttrib.M_none), 1000)

        buffer_cam.set_initial_state(initial_state.get_state())

        # Assign camera
        buffer_region = self._internal_buffer.get_display_region(0)
        buffer_region.set_camera(self._camera)
        buffer_region.set_active(True)
        buffer_region.disable_clears()

        self._node.flatten_strong()
        # self._node.ls()
        # self._node.analyze()

        self._active = True

    def remove_quad(self):
        """ Removes the fullscren quad after creation, this might be required
        when rendering to a scene which is not the main scene """
        self._quad.remove_node()
        self._quad = None

    def cleanup(self):
        """ Deletes this buffer, restoring the previous state """
        self._internal_buffer.clear_render_textures()
        self.engine.remove_window(self._internal_buffer)
        self._active = False

        if self._quad:
            self._quad.remove_node()

        for target in itervalues(self._targets):
            target.release_all()

    def make_main_target(self):
        """ Makes this target the main target which is show on screen """
        self._source_window.get_display_region(1).set_camera(self._camera)
        self.engine.remove_window(self._internal_buffer)
        self._internal_buffer.clear_render_textures()

        for i, region in enumerate(self._source_window.get_display_regions()):
            if i not in [1, 2, 4]:
                region.set_active(False)


    #
    # INTERNAL METHODS
    #


    def _find_main_region(self):
        """ Finds the assigned region of the main camera """
        for region in self._source_window.get_display_regions():
            if region.get_camera() == self._source_camera:
                return region
        return None

    def _create_buffer(self):
        pass

    def _make_fullscreen_quad(self):
        """ Create a quad which fills the whole screen """

        if self.use_oversized_triangle:
            vformat = GeomVertexFormat.get_v3()
            vdata = GeomVertexData("vertices", vformat, Geom.UH_static)
            vdata.set_num_rows(3)
            vwriter = GeomVertexWriter(vdata, "vertex")
            vwriter.add_data3f(-1, 0, -1)
            vwriter.add_data3f(3, 0, -1)
            vwriter.add_data3f(-1, 0, 3)
            gtris = GeomTriangles(Geom.UH_static)
            gtris.add_next_vertices(3)
            geom = Geom(vdata)
            geom.add_primitive(gtris)
            geom_node = GeomNode("gn")
            geom_node.add_geom(geom)
            quad = NodePath(geom_node)

        else:
            card = CardMaker("BufferQuad")
            card.set_frame_fullscreen_quad()
            quad = NodePath(card.generate())

        quad.set_depth_test(False)
        quad.set_depth_write(False)
        quad.set_attrib(TransparencyAttrib.make(TransparencyAttrib.M_none), 1000)
        quad.set_color(Vec4(1, 1, 1, 1))

        # Disable culling
        quad.node().set_final(True)
        quad.node().set_bounds(OmniBoundingVolume())
        quad.set_bin("unsorted", 10)
        return quad

    def _make_fullscreen_cam(self):
        """ Creates an orthographic camera for this buffer """
        buffer_cam = Camera("BufferCamera")
        lens = OrthographicLens()
        lens.set_film_size(2, 2)
        lens.set_film_offset(0, 0)
        lens.set_near_far(-1000, 1000)
        buffer_cam.set_lens(lens)
        buffer_cam.set_cull_bounds(OmniBoundingVolume())
        return buffer_cam

    def _create_buffer(self):
        """ Internal method to create the buffer object """
        # If the render target has a "normal" size, don't compute anything.
        # If the render target has a width / height of -1, use the
        # window width / height. If the render target has a width / height of < -1
        # use the window width / height divided by the absolute value of that
        # factor. E.g. a quarter-res buffer would have the size -4 / -4.
        win = self._source_window

        if self._size.x < 0:
            self._size.x = (win.get_x_size() - self._size.x - 1) // (-self._size.x)

        if self._size.y < 0:
            self._size.y = (win.get_y_size() - self._size.y - 1) // (-self._size.y)

        if not self._create():
            self.error("Failed to create buffer!")
            return False

        if self._source_region is None:
            self._source_region = self._internal_buffer.make_display_region()

    def _setup_textures(self):
        """ Preparse all bound textures """
        for i in range(self._aux_count):
            self._targets["aux_{}".format(i)] = Texture(
                self.debug_name + "_aux{}".format(i))
        for name, tex in iteritems(self._targets):
            tex.set_wrap_u(SamplerState.WM_clamp)
            tex.set_wrap_v(SamplerState.WM_clamp)
            tex.set_anisotropic_degree(0)
            tex.set_x_size(self._size.x)
            tex.set_y_size(self._size.y)
            tex.set_minfilter(SamplerState.FT_linear)
            tex.set_magfilter(SamplerState.FT_linear)

    def _make_properties(self):
        """ Creates the window and buffer properties """
        window_props = WindowProperties.size(self._size.x, self._size.y)
        buffer_props = FrameBufferProperties()

        if self._color_bits == (16, 16, 16, 0):
            buffer_props.set_rgba_bits(11, 11, 10, 0)
        else:
            buffer_props.set_rgba_bits(*self._color_bits)

        buffer_props.set_accum_bits(0)
        buffer_props.set_stencil_bits(0)
        buffer_props.set_back_buffers(0)
        buffer_props.set_coverage_samples(0)
        buffer_props.set_depth_bits(self._depth_bits)
        buffer_props.set_float_depth(True)
        buffer_props.set_float_color(max(self._color_bits) > 8)
        buffer_props.set_force_hardware(True)
        buffer_props.set_multisamples(0)
        buffer_props.set_srgb_color(False)
        buffer_props.set_stereo(False)
        buffer_props.set_stencil_bits(0)

        if self._aux_bits == 8:
            buffer_props.set_aux_rgba(self._aux_count)
        elif self._aux_bits == 16:
            buffer_props.set_aux_hrgba(self._aux_count)
        elif self._aux_bits == 32:
            buffer_props.set_aux_float(self._aux_count)
        else:
            self.error("Invalid aux bits")

        return window_props, buffer_props

    def _create(self):
        """ Creates the internally used buffer """
        self._setup_textures()
        window_props, buffer_props = self._make_properties()

        self._internal_buffer = self.engine.make_output(
            self._source_window.get_pipe(), self.debug_name, 1,
            buffer_props, window_props, GraphicsPipe.BF_refuse_window,
            self._source_window.get_gsg(), self._source_window)

        if not self._internal_buffer:
            self.error("Failed to create buffer")
            return

        if self._depth_bits:
            self._internal_buffer.add_render_texture(
                self.depth_tex, GraphicsOutput.RTM_bind_or_copy,
                GraphicsOutput.RTP_depth)

        if self._color_bits.count(0) != 4:
            self._internal_buffer.add_render_texture(
                self.color_tex, GraphicsOutput.RTM_bind_or_copy,
                GraphicsOutput.RTP_color)

        aux_prefix = {
            8: "RTP_aux_rgba_{}",
            16: "RTP_aux_hrgba_{}",
            32: "RTP_aux_float_{}",
        }[self._aux_bits]

        for i in range(self._aux_count):
            target_mode = getattr(GraphicsOutput, aux_prefix.format(i))
            self._internal_buffer.add_render_texture(
                self.aux_tex[i], GraphicsOutput.RTM_bind_or_copy, target_mode)

        sort = -300 + RenderTarget._NUM_BUFFERS_ALLOCATED * 10
        RenderTarget._NUM_BUFFERS_ALLOCATED += 1
        self._internal_buffer.set_sort(sort)
        self._internal_buffer.disable_clears()
        self._internal_buffer.get_display_region(0).disable_clears()

        BufferViewer.register_entry(self)

        return True
