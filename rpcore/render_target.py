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

# Disable the warning from pylint about not finding the "base" builtin provided
# from Panda3D
# pylint: disable=E0602


from __future__ import print_function

from panda3d.core import GraphicsOutput, CardMaker, OmniBoundingVolume, Texture
from panda3d.core import AuxBitplaneAttrib, NodePath, OrthographicLens, Geom
from panda3d.core import Camera, Vec4, TransparencyAttrib, StencilAttrib
from panda3d.core import ColorWriteAttrib, DepthWriteAttrib, GeomVertexData
from panda3d.core import WindowProperties, FrameBufferProperties, GraphicsPipe
from panda3d.core import GeomVertexFormat, GeomNode, GeomVertexWriter
from panda3d.core import GeomTriangles, SamplerState

__all__ = ["RenderTarget"]

class RenderTargetType(object):

    """ This stores the possible types of targets beeing able
    to be attached to a RenderTarget. Python does not support
    enums (yet) so this is a class. """

    COLOR = "color"
    DEPTH = "depth"
    AUX_0 = "aux0"
    AUX_1 = "aux1"
    AUX_2 = "aux2"
    AUX_3 = "aux3"

    def __init__(self):
        raise NotImplementedError("Class is static!")

RenderTargetType.ALL = "depth color aux0 aux1 aux2 aux3".split()

# Function Decorator which is used to specify whether the function is supposed
# to be called "before" creating the target, or "after" creating the target
def require_created(func):
    def func_wrapper(*args, **kwargs):
        if len(args) > 0 and isinstance(args[0], RenderTarget):
            args[0]._require_created()
        return func(*args, **kwargs)
    return func_wrapper

def require_uncreated(func):
    def func_wrapper(*args, **kwargs):
        if len(args) > 0 and isinstance(args[0], RenderTarget):
            args[0]._require_not_created()
        return func(*args, **kwargs)
    return func_wrapper


class RenderTarget(object):

    """ This is a high level interface for creating buffers
    and render-to-textures. It internally wraps around Panda3Ds buffer interface
    but also takes care of sorting and clearing, and especially
    setting up the scene rendering when using render-to-texture.

    For a detailed description and setup check out the README here:

    https://github.com/tobspr/RenderTarget

    """

    # This variable can be set to a function handle and will get called whenever
    # a new render target gets created
    RT_CREATE_HANDLER = lambda handle: 0

    # This variable can be used to redirect the stdout output of the render
    # target. The function should be a function which takes a variable amount
    # of parameters, such as the print function. If you don't want to recieve
    # messages from the render target, set this to an empty function or lambda.
    RT_OUTPUT_FUNC = print

    # Whether to use an oversized triangle instead of quads. Theoretically this is
    # faster, since overshading at the diagonal of the quad is avoided, since the
    # quad is internally converted into two triangles. In practice, this depends,
    # and leads to almost no performance gain, however, it certainly doesn't hurt,
    # too. Keep in mind you have to adjust your vertex shaders if you do not
    # use this option! (Replace p3d_Vertex.y by p3d_Vertex.z)
    USE_OVERSIZED_TRIANGLE = True

    # Whether to automatically use the GL_R11_G11_B10 format for targets with
    # 16 bit color and no color alpha. This results in a tiny bit of lost precision,
    # however it has a much smaller memory footprint (about half size).
    USE_R11_G11_B10 = True

    # Internal variable to store the number of allocated buffers to give them a
    # unique sort index.
    _NUM_BUFFERS_ALLOCATED = 0

    @classmethod
    def get_num_buffers(cls):
        """ Returns the amount of buffers which have been allocated yet """
        return cls._NUM_BUFFERS_ALLOCATED

    def __init__(self, name="DefaultRT"):
        """ Creates a new RenderTarget with the given name. Use a
        descriptive name as it will show with this name in pstats. """
        self._targets = {}
        self._bind_mode = GraphicsOutput.RTMBindOrCopy
        self._depth_bits = 32
        self._color_bits = 8
        self._aux_bits = 8
        self._use_stencil = False
        self._quad = None
        self._source_cam = base.cam
        self._source_window = base.win
        self._width = -1
        self._height = -1
        self._name = name
        self._region = self._find_region_for_camera()
        self._enable_transparency = False
        self._layers = 0
        self._create_overlay_quad = True
        self._write_color = False
        self._multisamples = 0
        self._engine = base.graphicsEngine
        self._active = False
        self._use_texture_arrays = False
        self._have_color_alpha = False
        self._internal_buffer = None
        self._camera = None
        self._node = None
        self._created = False

    def __getitem__(self, name):
        """ Handy function to be able to to RenderTarget["color"] instead of
        RenderTarget._get_target("color"). This is the preferred (and only) way
        to access the render target textures. """
        return self._get_target(name)

    def __setattr__(self, name, value):
        """ Setter method, allows to do .attr = x when a set_attr method exists. """
        if "set_" + name in self.__class__.__dict__:
            if not isinstance(value, (tuple, list)):
                value = [value,]
            self.__class__.__dict__["set_" + name](*([self] + list(value)))
        else:
            if not name.startswith("_") and not name[0].isupper():
                raise Exception("RenderTarget has no attribute '" + name + "'")
            self.__dict__[name] = value

    def __getattr__(self, name):
        """ Getter method, allows to do .attr when a get_attr method exists. """
        if "get_" + name in self.__class__.__dict__:
            return self.__class__.__dict__["get_" + name](self)
        return self.__dict__[name]

    def _require_created(self):
        """ This is an internal function which gets called to ensure the render
        target is created, and otherwise throws an error """
        if not self._created:
            raise Exception("ERROR: You called a function which requires the "
                            "RenderTarget to be created, but it is not created yet!")

    def _require_not_created(self):
        """ This is an internal function which gets called to ensure the render
        target is *not* created yet. If its already created, an exception will be
        raised """
        if self._created:
            raise Exception("ERROR: You called a function which is supposed to "
                            "be called when the RenderTarget is not created "
                            "yet, however it is already created!")

    @require_uncreated
    def set_create_overlay_quad(self, create_quad):
        """ When create quad is set to true, a fullscreen quad will be used to be
        able to directly apply a shader to it """
        self._create_overlay_quad = create_quad

    @require_uncreated
    def set_has_color_alpha(self, color_alpha):
        """ Sets Whether the color buffer has an alpha channel or not """
        self._have_color_alpha = color_alpha

    @require_uncreated
    def set_use_texture_arrays(self, state=True):
        """ Makes the render buffer use a 2D texture array when rendering
        layers. Otherwise a 3D Texture is choosen """
        self._use_texture_arrays = state

    @require_uncreated
    def set_multisamples(self, samples):
        """ Sets the amount of multisamples to use """
        self._multisamples = samples

    @require_uncreated
    def set_engine(self, engine):
        """ Sets the graphic engine to use """
        self._engine = engine

    @require_uncreated
    def set_layers(self, layers):
        """ Sets the number of layers. When greater than 1, this enables
        rendering to a texture array or 3D texture."""
        self._layers = layers
        if layers > 1:
            self._bind_mode = GraphicsOutput.RTMBindLayered

    def set_name(self, name):
        """ Sets the buffer name to identify it in pstats """
        self._name = name

    @require_uncreated
    def set_enable_transparency(self, enabled=True):
        """ Sets Whether objects can be transparent in this buffer """
        self._enable_transparency = enabled

    @require_uncreated
    def set_size(self, width, height=None):
        """ Sets the buffer size in pixels. -1 means as big as the current
        window (default) """
        self._width = width

        if height is None:
            height = width

        self._height = height

    @require_uncreated
    def set_half_resolution(self):
        """ Sets the buffer to render at half the size of the window """
        self._width = -2
        self._height = -2

    @require_uncreated
    def set_quarter_resolution(self):
        """ Sets the buffer to render at half the size of the window """
        self._width = -4
        self._height = -4

    @require_uncreated
    def set_color_write(self, write):
        """ Sets Whether to write color """
        self._write_color = write

    @require_uncreated
    def set_color_bits(self, color_bits):
        """ Sets the amount of color bits to request """
        self._color_bits = color_bits

    @require_uncreated
    def set_use_stencil(self, flag=True):
        """ Sets whether to use a stencil buffer (stored in the depth buffer) """
        self._use_stencil = flag

    @require_uncreated
    def set_aux_bits(self, aux_bits):
        """ Sets the amount  of auxiliary bits to request """
        self._aux_bits = aux_bits

    @require_uncreated
    def set_depth_bits(self, bits):
        """ Sets the amount of depth bits to request """
        self._depth_bits = bits

    @require_created
    def make_main_target(self):
        """ Makes this target show on screen """
        self._source_window.get_display_region(1).set_camera(self._camera)
        self._engine.remove_window(self._internal_buffer)
        self._internal_buffer.clear_render_textures()

        for idx in range(self._source_window.get_num_display_regions()):
            region = self._source_window.get_display_region(idx)
            if idx not in [1, 2, 4]:
                # overlay display region
                region.set_active(False)

    @require_created
    def set_shader_input(self, *args):
        """ This is a shortcut for setting shader inputs on the buffer """
        self.get_node().set_shader_input(*args)

    @require_created
    def set_attrib(self, *args):
        """ This is a shortcut for setting render attributes on the buffer """
        self.get_node().set_attrib(*args)

    @require_created
    def set_shader(self, shader):
        """ This is a shortcut for setting shaders to the buffer """
        self.get_node().set_shader(shader)

    @require_created
    def get_color_texture(self):
        """ Returns the handle to the color texture """
        self.RT_OUTPUT_FUNC("Deprecated: get_color_texture, use obj['color'] instead")
        return self.get_texture(RenderTargetType.COLOR)

    @require_created
    def get_depth_texture(self):
        """ Returns the handle to the depth texture """
        self.RT_OUTPUT_FUNC("Deprecated: get_depth_texture, use obj['depth'] instead")
        return self.get_texture(RenderTargetType.DEPTH)

    @require_created
    def get_internal_buffer(self):
        """ Returns the internal buffer object """
        return self._internal_buffer

    @require_created
    def get_internal_region(self):
        """ Returns the internal display region, this can be used to set
        custom sort values."""
        return self._internal_buffer.get_display_region(0)

    @require_created
    def get_aux_texture(self, index=0):
        """ Returns the n-th aux texture, starting at 0 """
        assert index < 4
        self.RT_OUTPUT_FUNC("Deprecated: get_aux_texture, use obj['aux<n>'] instead")
        return self.get_texture(getattr(RenderTargetType, "AUX_" + str(index)))

    @require_uncreated
    def set_source(self, source_cam, source_win, region=None):
        """ Sets source window and camera. When region is None, it will
        be set automatically (highly recommended) """
        self._source_cam = source_cam
        self._source_window = source_win
        self._region = region

    @require_uncreated
    def load_stencil(self, depth_stencil_tex):
        """ Makes this target use the stencil texture from another pass """
        self.set_use_stencil(True)
        self._targets["depth"] = depth_stencil_tex

    @require_uncreated
    def set_bind_mode_layered(self, layered=True):
        """ When rendering layered, you have to call this. This
        sets the internal bind mode for the RenderBuffer. When not using
        layered bind mode, the rendering might get very slow. """
        if layered:
            self._bind_mode = GraphicsOutput.RTM_bind_layered
        else:
            self._bind_mode = GraphicsOutput.RTM_bind_or_copy

    @require_uncreated
    def add_render_texture(self, target_type):
        """ Lower level function to add a new target. target_type should be
        a RenderTargetType """
        if target_type in self._targets:
            self.RT_OUTPUT_FUNC("You cannot add another type of", target_type)
            return False
        self._targets[target_type] = Texture((self._name +
                                              target_type[0].upper() +
                                              target_type[1:]).replace(" ", ""))
        if target_type == RenderTargetType.COLOR:
            self._write_color = True

    @require_uncreated
    def add_color_texture(self, bits=None):
        """ Adds a color target """
        self.add_render_texture(RenderTargetType.COLOR)
        if bits:
            self.set_color_bits(bits)

    @require_uncreated
    def add_depth_texture(self, bits=None):
        """ Adds a depth target """
        self.add_render_texture(RenderTargetType.DEPTH)
        if bits:
            self.set_depth_bits(bits)

    @require_uncreated
    def add_color_and_depth(self, color_bits=None, depth_bits=None):
        """ Adds a color and depth target """
        self.add_color_texture(color_bits)
        self.add_depth_texture(depth_bits)

    @require_uncreated
    def add_aux_textures(self, num, bits=None):
        """ Adds n aux textures. num should be between 1 and 4. This overrides
        the previous number of aux textures set! Theoretically this function
        behaves like set_aux_textures(), but for convenience its called
        add_aux_textures. """
        assert num > 0 and num <= 4
        for i in range(num):
            self.add_render_texture(getattr(RenderTargetType, "AUX_" + str(i)))
        if bits:
            self.set_aux_bits(bits)

    @require_uncreated
    def add_aux_texture(self, bits=None):
        """ Adds a single aux texture, equivalent to add_aux_textures(1). """
        self.add_aux_textures(1, bits)

    def get_all_targets(self):
        """ Returns all attached targets """
        targets = []
        for target in RenderTargetType.ALL:
            if self.has_target(target):
                targets.append(target)
        return targets

    def has_target(self, target):
        """ Check if a target is assigned to this target """
        return target in self._targets

    def has_aux_textures(self):
        """ Returns Whether this target has at least 1 aux texture attached """
        return self.has_target(RenderTargetType.AUX_0)

    def has_color_texture(self):
        """ Returns Whether this target has a color texture attached """
        return self.has_target(RenderTargetType.COLOR)

    def has_depth_texture(self):
        """ Returns Whether this target has a depth texture attached """
        return self.has_target(RenderTargetType.DEPTH)

    @require_created
    def get_region(self):
        """ Returns the display region of this target. You can use
        this to set custom clears """
        return self._region

    @require_uncreated
    def prepare_scene_render(self, early_z=False, early_z_cam=None):
        """ Renders the scene of the source camera to the buffer. See the
        documentation of this class for further information """

        # Init buffer object
        self._create_buffer()

        # Prepare initial state
        initial_state = NodePath("initial_stateDummy")

        if self._source_cam:
            initial_state.set_state(self._source_cam.node().get_initial_state())

        if self.has_target(RenderTargetType.AUX_0):
            initial_state.set_attrib(AuxBitplaneAttrib.make(self._aux_bits), 20)

        initial_state.set_attrib(StencilAttrib.make_off(), 10)

        if not self._enable_transparency:
            initial_state.set_attrib(
                TransparencyAttrib.make(TransparencyAttrib.M_none), 100)

        if not self._write_color:
            initial_state.set_attrib(ColorWriteAttrib.make(ColorWriteAttrib.C_off), 100)

        if self._source_cam:
            self._source_cam.node().set_initial_state(initial_state.get_state())

        if early_z:
            self._early_z_region = self._internal_buffer.make_display_region()
            self._early_z_region.set_sort(-10)
            self._early_z_region.set_camera(early_z_cam)

        self._node = NodePath("RTRoot")

        # Prepare fullscreen quad
        if self._create_overlay_quad:

            self._quad = self._make_fullscreen_quad()
            self._quad.reparent_to(self._node)

            buffer_cam = self._make_fullscreen_cam()
            self._camera = self._node.attach_new_node(buffer_cam)
            self._region.set_camera(self._camera)
            self._region.set_sort(5)

        else:
            self._region.set_active(False)

        # Set clears
        buffer_region = self._internal_buffer.get_display_region(0)
        self._correct_clears()

        buffer_region.set_clear_stencil_active(False)

        # Set aux clears
        for i in range(4):
            target = getattr(RenderTargetType, "AUX_" + str(i))
            target_bind_pos = getattr(GraphicsOutput, "RTP_aux_rgba_" + str(i))
            if self.has_target(target):
                buffer_region.set_clear_active(target_bind_pos, 1)
                buffer_region.set_clear_value(
                    target_bind_pos, Vec4(0.5, 0.5, 1.0, 0.0))

        self._region.disable_clears()

        if self._source_cam:
            buffer_region.set_camera(self._source_cam)
            buffer_region.set_active(1)

        buffer_region.set_sort(20)

        if early_z:
            buffer_region.set_clear_depth_active(False)
            self._early_z_region.disable_clears()
            self._early_z_region.set_clear_depth_active(True)
            self._early_z_region.set_active(1)

        self._set_size_shader_input()

        self._active = True
        self._register_buffer()

    @require_uncreated
    def prepare_offscreen_buffer(self):
        """ Creates an offscreen buffer for this target """

        # Init buffer object
        self._create_buffer()

        # Prepare fullscreen quad
        self._node = NodePath("RTRoot")
        self._quad = self._make_fullscreen_quad()
        self._quad.reparent_to(self._node)

        # Prepare fullscreen camera
        buffer_cam = self._make_fullscreen_cam()
        initial_state = NodePath("is")

        if not self._write_color:
            initial_state.set_attrib(
                ColorWriteAttrib.make(ColorWriteAttrib.C_off), 1000)

        initial_state.set_attrib(
            DepthWriteAttrib.make(DepthWriteAttrib.M_none), 1000)

        initial_state.set_attrib(StencilAttrib.make_off(), 10)

        buffer_cam.set_initial_state(initial_state.get_state())
        self._camera = self._node.attach_new_node(buffer_cam)

        buffer_region = self._internal_buffer.get_display_region(0)
        buffer_region.set_camera(self._camera)
        buffer_region.set_active(1)
        buffer_region.set_clear_stencil_active(False)
        self._set_size_shader_input()

        self._active = True
        self._register_buffer()

    @require_created
    def set_active(self, active):
        """ You can enable / disable the buffer with this. When disabled,
        shaders on this buffer aren't executed """
        if self._active is not active:
            for region in self._internal_buffer.get_display_regions():
                if region != self._internal_buffer.get_overlay_display_region():
                    region.set_active(active)
            self._active = active

    @require_created
    def get_quad(self):
        """ Returns the quad-node path. You can use this to set attributes on it """
        return self._quad

    @require_created
    def get_node(self):
        """ Returns the buffer top node path, where the quad and camera is parented
        to """
        return self._node

    @require_created
    def get_effective_width(self):
        """ Returns the width of the render target in pixels """
        return self._width

    @require_created
    def get_effective_height(self):
        """ Returns the height of the render target in pixels """
        return self._height

    def get_texture(self, target):
        """ Returns the texture assigned to a target. The target should be a
        RenderTargetType """
        if target not in self._targets:
            self.RT_OUTPUT_FUNC("The target", target, "isn't bound to this RenderTarget!")
            return
        return self._get_target(target)

    @require_created
    def set_clear_depth(self, clear=True, force=False):
        """ Adds a depth clear """
        self._internal_buffer.set_clear_depth_active(clear)
        if clear:
            self._internal_buffer.set_clear_depth(1.0)
            if not self.has_depth_texture():
                self.RT_OUTPUT_FUNC("Warning: clear=True set on target without depth attachment!")
        if force:
            self.get_internal_region().set_clear_depth(clear)

    @require_created
    def set_clear_color(self, clear=True, color=None):
        """ Adds a color clear """
        self.get_internal_region().set_clear_color_active(clear)
        self._internal_buffer.set_clear_color_active(clear)

        if clear:
            if color is None:
                color = Vec4(1, 0, 1, 1)
            # self._internal_buffer.set_clear_color(color)
            self.get_internal_region().set_clear_color(color)

            if not self.has_color_texture():
                self.RT_OUTPUT_FUNC("Warning: clear=True set on target without color attachment!")

    @require_created
    def set_clear_stencil(self, clear=True, stencil=0x00):
        """ Sets whether to clear the stencil buffer """
        self.get_internal_region().set_clear_stencil_active(clear)
        self._internal_buffer.set_clear_stencil_active(clear)

        if clear:
            # self._internal_buffer.set_clear_stencil(stencil)
            self.get_internal_region().set_clear_stencil(stencil)

    @require_created
    def remove_quad(self):
        """ Removes the fullscren quad after creation, this might be required
        when rendering to a scene which is not the main scene """
        self.get_quad().remove_node()

    @require_created
    def is_active(self):
        """ Returns Whether this buffer is currently active """
        return self._active

    @require_created
    def delete_buffer(self):
        """ Deletes this buffer, restoring the previous state """
        self._internal_buffer.clear_render_textures()
        self._engine.remove_window(self._internal_buffer)
        self._active = False

        if self._create_overlay_quad:
            self._quad.remove_node()

        for target in RenderTargetType.ALL:
            if self.has_target(target):
                tex = self._get_target(target)
                tex.release_all()

    def _get_target(self, target):
        """ Returns the texture handle for the given target """
        return self._targets[target]

    def _make_fullscreen_quad(self):
        """ Create a quad which fills the whole screen """

        if self.USE_OVERSIZED_TRIANGLE:

            # Create an oversized triangle
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
            # Create a simple quad
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

    def _find_region_for_camera(self):
        """ Finds the assigned region of the supplied camera """
        for i in range(self._source_window.get_num_display_regions()):
            region = self._source_window.get_display_region(i)
            drcam = region.get_camera()
            if drcam == self._source_cam:
                return region
        return None

    def _correct_clears(self):
        """ Setups the clear values correctly for the buffer region """
        region = self._internal_buffer.get_display_region(0)

        clears = []

        for i in range(GraphicsOutput.RTPCOUNT):
            active, value = self._source_window.get_clear_active(
                i), self._source_window.get_clear_value(i)

            if not active:
                active, value = self._region.get_clear_active(
                    i), self._region.get_clear_value(i)

            region.set_clear_active(i, active)
            region.set_clear_value(i, value)

        return clears

    def _set_size_shader_input(self):
        """ Makes the buffer size available as shader input in the shader """
        if self._create_overlay_quad:
            size_input = Vec4(1.0 / self._width, 1.0 / self._height,
                              self._width, self._height)
            self.set_shader_input("bufferSize", size_input)

    def _register_buffer(self):
        """ Internal method to register the buffer at the create handler """
        RenderTarget.RT_CREATE_HANDLER(self)

    def _create_buffer(self):
        """ Internal method to create the buffer object """

        # If the render target has a "normal" size, don't compute anything.
        # If the render target has a width / height of -1, use the
        # window width / height. If the render target has a width / height of < -1
        # use the window width / height divided by the absolute value of that factor.
        # A quarter-res buffer e.g. would have the size -4 / -4.

        if self._width < 0:
            self._width = (self._source_window.get_x_size() - self._width - 1) // (-self._width)

        if self._height < 0:
            self._height = (self._source_window.get_y_size() - self._height - 1) // (-self._height)

        if not self._create():
            self.RT_OUTPUT_FUNC("Failed to create buffer!")
            return False

        if self._region is None:
            self._region = self._internal_buffer.make_display_region()

    def _create(self):
        """ Attempts to create this buffer """

        if not isinstance(self._color_bits, (list, tuple)):
            self._color_bits = [self._color_bits] * 3 +\
                               [self._color_bits if self._have_color_alpha else 0]
        color_is_float = max(self._color_bits) >= 16

        # set wrap modes for color + auxtextures,
        # also set correct formats:
        # panda doesnt use sized formats automatically, this
        # gives problems when using imageLoad / imageStore
        prepare = list(RenderTargetType.ALL)

        # Don't prepare the depth texture here
        prepare.remove(RenderTargetType.DEPTH)

        for target in prepare:
            if not self.has_target(target):
                continue
            handle = self._get_target(target)
            handle.set_wrap_u(SamplerState.WM_clamp)
            handle.set_wrap_v(SamplerState.WM_clamp)
            handle.set_wrap_w(SamplerState.WM_clamp)
            handle.set_minfilter(SamplerState.FT_linear)
            handle.set_magfilter(SamplerState.FT_linear)
            handle.set_anisotropic_degree(0)
            handle.set_x_size(self._width)
            handle.set_y_size(self._height)

            if target == RenderTargetType.COLOR:
                if color_is_float:
                    handle.set_component_type(Texture.T_float)
            else:
                if self._aux_bits > 8:
                    handle.set_component_type(Texture.T_float)

            if self._layers > 1:
                if self._use_texture_arrays:
                    handle.setup_2d_texture_array(self._layers)
                else:
                    handle.setup_3d_texture(self._layers)

        # set layers for depth texture
        if self._layers > 1 and self.has_target(RenderTargetType.DEPTH):
            if self._use_texture_arrays:
                self._get_target(RenderTargetType.DEPTH).setup_2d_texture_array(
                    self._layers)
            else:
                self._get_target(RenderTargetType.DEPTH).setup_3d_texture(
                    self._layers)

        # Create buffer descriptors
        window_props = WindowProperties.size(self._width, self._height)
        buffer_props = FrameBufferProperties()

        # Set color and alpha bits
        if self.has_target(RenderTargetType.COLOR):

            # Special case for r11g11b10
            if self.USE_R11_G11_B10 and self._color_bits == [16, 16, 16, 0]:
                buffer_props.set_rgba_bits(11, 11, 10, 0)
            else:
                buffer_props.set_rgba_bits(*self._color_bits)

            if color_is_float:
                buffer_props.set_float_color(True)
        else:
            buffer_props.set_rgba_bits(0, 0, 0, 0)

        buffer_props.set_stencil_bits(0)

        # Set depth bits and depth texture format
        if self.has_target(RenderTargetType.DEPTH):
            depth_target = self._get_target(RenderTargetType.DEPTH)

            if not self._use_stencil:
                buffer_props.set_depth_bits(self._depth_bits)
                buffer_props.set_float_depth(self._depth_bits == 32)
            else:
                if self._depth_bits != 32:
                    self.RT_OUTPUT_FUNC("You should use 32 bit depth when using stencil ("
                                        "will get 24 bits effectively)")
                buffer_props.set_depth_bits(24)
                buffer_props.set_float_depth(False)
                buffer_props.set_stencil_bits(8)

            depth_target.set_x_size(self._width)
            depth_target.set_y_size(self._height)
            depth_target.set_wrap_u(SamplerState.WM_clamp)
            depth_target.set_wrap_v(SamplerState.WM_clamp)

        else:
            if self._use_stencil:
                self.RT_OUTPUT_FUNC("Stencil enabled but no depth texture attached!")
            buffer_props.set_depth_bits(0)

        # Set stencil bits
        num_auxtex = 0

        for i in range(4):
            if self.has_target(getattr(RenderTargetType, "AUX_" + str(i))):
                num_auxtex = i + 1

        # Add aux textures
        if self._aux_bits == 32:
            buffer_props.set_aux_float(num_auxtex)
        elif self._aux_bits == 16:
            buffer_props.set_aux_hrgba(num_auxtex)
        elif self._aux_bits == 8:
            buffer_props.set_aux_rgba(num_auxtex)
        else:
            self.RT_OUTPUT_FUNC("Invalid amount of auxiliary bits!")
            return

        buffer_props.set_multisamples(self._multisamples)

        # Create internal graphics output
        self._internal_buffer = self._engine.make_output(
            self._source_window.get_pipe(), self._name, 1,
            buffer_props, window_props,
            GraphicsPipe.BF_refuse_window,
            self._source_window.get_gsg(), self._source_window)

        if self._internal_buffer is None:
            self.RT_OUTPUT_FUNC("Failed to create buffer :(")
            return False

        # Add render targets
        if self.has_target(RenderTargetType.DEPTH):
            self._internal_buffer.add_render_texture(
                self._get_target(RenderTargetType.DEPTH), self._bind_mode,
                GraphicsOutput.RTP_depth_stencil if self._use_stencil else GraphicsOutput.RTP_depth)

        if self.has_target(RenderTargetType.COLOR):
            self._internal_buffer.add_render_texture(
                self._get_target(RenderTargetType.COLOR), self._bind_mode,
                GraphicsOutput.RTP_color)

        for i in range(4):
            target = getattr(RenderTargetType, "AUX_" + str(i))
            if self.has_target(target):

                if self._aux_bits == 32:
                    target_mode = getattr(GraphicsOutput, "RTP_aux_float_" + str(i))
                elif self._aux_bits == 16:
                    target_mode = getattr(GraphicsOutput, "RTP_aux_hrgba_" + str(i))
                else:
                    target_mode = getattr(GraphicsOutput, "RTP_aux_rgba_" + str(i))
                self._internal_buffer.add_render_texture(
                    self._get_target(target), self._bind_mode, target_mode)

        # Increment global sort counter and assign a unique sort
        RenderTarget._NUM_BUFFERS_ALLOCATED += 1
        self._sort = -300 + RenderTarget._NUM_BUFFERS_ALLOCATED * 10

        self._internal_buffer.set_sort(self._sort)
        self._internal_buffer.disable_clears()
        self._internal_buffer.get_display_region(0).disable_clears()

        for i in range(16):
            self._internal_buffer.set_clear_active(i, False)
            self._internal_buffer.get_display_region(0).set_clear_active(i, False)

        self._internal_buffer.set_clear_stencil_active(False)

        # Set proper depth format again, dunno why panda needs this.
        if self.has_target(RenderTargetType.DEPTH):
            depth_target = self._get_target(RenderTargetType.DEPTH)
            depth_target.set_format(
                getattr(Texture, "F_depth_component" + str(self._depth_bits)))

        self._created = True

        self._internal_buffer.get_overlay_display_region().disable_clears()
        self._internal_buffer.get_overlay_display_region().set_active(False)

        return True

    def __repr__(self):
        """ Returns a representative string of this instance """
        return "RenderTarget('" + self._name + "')"
