

from panda3d.core import GraphicsOutput, CardMaker, OmniBoundingVolume
from panda3d.core import AuxBitplaneAttrib, NodePath, OrthographicLens
from panda3d.core import Camera, Vec4, TransparencyAttrib, StencilAttrib
from panda3d.core import ColorWriteAttrib, DepthWriteAttrib, Texture
from panda3d.core import WindowProperties, FrameBufferProperties, GraphicsPipe

# from MemoryMonitor import MemoryMonitor
from DebugObject import DebugObject
from ..Globals import Globals
from ..GUI.BufferViewer import BufferViewer


class RenderTargetType:

    """ This stores the possible types of targets beeing able
    to be attached to a RenderTarget. Python does not support
    enums (yet) so this is a class. """

    COLOR = "color"
    DEPTH = "depth"
    AUX_0 = "aux0"
    AUX_1 = "aux1"
    AUX_2 = "aux2"
    AUX_3 = "aux3"

    ALL = ["depth", "color", "aux0", "aux1", "aux2", "aux3"]


class RenderTarget(DebugObject):

    """ This is a high level interface for creating buffers
    and render-to-textures. It internally wraps around RenderBuffer
    but also takes care of sorting and clearing, and especially
    setting up the scene rendering when using render-to-texture.

    After creating a RenderTarget, you have to add targets with
    add_render_texture, with target beeing RenderTargetType.XXX. There
    are shortcuts for this like add_color_texture and add_depth_texture.

    When not setting a size, the size will be the size of the specified
    window (set with set_source, default is base.win). Using set_size(-1, -1)
    has the same effect.

    Then you can either call prepare_scene_render(), which will render
    the scene of the sourceCam (set with set_source, default is base.cam)
    to the buffer, or call prepare_offscreen_buffer(), which will just
    create an offscreen buffer.

    A sample setup might look like this:

        target = RenderTarget("My Fancy Target")

        # This adds RenderTargetType.COLOR and RenderTargetType.DEPTH
        target.add_color_and_depth()

        # This adds RenderTargetType.AUX_0 and RenderTargetType.AUX_1
        target.add_aux_textures(2)
        target.set_aux_bits(16)
        target.set_color_bits(16)
        target.set_depth_bits(32)
        target.prepare_scene_render()

    """

    _NUM_BUFFERS_ALLOCATED = 0

    def __init__(self, name="DefaultRT"):
        """ Creates a new RenderTarget with the given name. Use a
        descriptive name as it will show with this name in pstats """
        DebugObject.__init__(self, "RenderTarget")
        self._targets = {}
        self._bind_mode = GraphicsOutput.RTMBindOrCopy
        self._depth_bits = 16
        self._quad = None
        self._source_cam = Globals.base.cam
        self._source_window = Globals.base.win
        self._width = -1
        self._height = -1
        self._name = name
        self._color_bits = 8
        self._aux_bits = 8
        self._region = self._find_region_for_camera()
        self._enable_transparency = False
        self._layers = 0
        self._create_overlay_quad = True
        self._write_color = True
        self._multisamples = 0
        self._engine = Globals.base.graphicsEngine
        self._active = False
        self._use_texture_arrays = False
        self._have_color_alpha = True
        self._internal_buffer = None
        self._camera = None
        self._node = None
        self._rename(name)
        self.mute()

    def __getitem__(self, name):
        """ Handy function to be able to to RenderTarget["color"] instead of
        RenderTarget.get_target("color") """
        return self.get_target(name)

    def set_create_overlay_quad(self, create_quad):
        """ When create quad is set to true, a fullscreen quad will be used to be
        able to directly apply a shader to it """
        self._create_overlay_quad = create_quad

    def set_have_color_alpha(self, color_alpha):
        """ Sets Whether the color buffer has an alpha channel or not """
        self._have_color_alpha = color_alpha

    def set_use_texture_arrays(self, state=True):
        """ Makes the render buffer use a 2D texture array when rendering
        layers. Otherwise a 3D Texture is choosen """
        self._use_texture_arrays = state

    def set_multisamples(self, samples):
        """ Sets the amount of multisamples to use """
        self._multisamples = samples

    def set_engine(self, engine):
        """ Sets the graphic engine to use """
        self._engine = engine

    def set_layers(self, layers):
        """ Sets the number of layers. When greater than 1, this enables
        rendering to a texture array or 3D texture."""
        self._layers = layers
        if layers > 1:
            self._bind_mode = GraphicsOutput.RTMBindLayered

    def set_name(self, name):
        """ Sets the buffer name to identify it in pstats """
        self._name = name

    def set_enable_transparency(self, enabled=True):
        """ Sets Whether objects can be transparent in this buffer """
        self._enable_transparency = enabled

    def set_size(self, width, height=None):
        """ Sets the buffer size in pixels. -1 means as big as the current
        window (default) """
        self._width = width

        if height is None:
            height = width

        self._height = height

    def set_half_resolution(self):
        """ Sets the buffer to render at half the size of the window """
        self._width = (Globals.resolution.x + 1) / 2
        self._height = (Globals.resolution.y + 1) / 2

    def set_quarter_resolution(self):
        """ Sets the buffer to render at half the size of the window """
        self._width = (Globals.resolution.x + 3) / 4
        self._height = (Globals.resolution.y + 3) / 4

    def set_color_write(self, write):
        """ Sets Whether to write color """
        self._write_color = write

    def set_color_bits(self, color_bits):
        """ Sets the amount of color bits to request """
        self._color_bits = color_bits

    def set_aux_bits(self, aux_bits):
        """ Sets the amount  of auxiliary bits to request """
        self._aux_bits = aux_bits

    def set_depth_bits(self, bits):
        """ Sets the amount of depth bits to request """
        self._depth_bits = bits

    def make_main_target(self):
        """ Makes this target show on screen """
        Globals.base.win.get_display_region(1).set_camera(self._camera)
        self._engine.remove_window(self._internal_buffer)
        self._internal_buffer.clear_render_textures()

        # Globals.base.win.get_display_region(2).set_active(False)
        for idx in xrange(Globals.base.win.get_num_display_regions()):
            dr = Globals.base.win.get_display_region(idx)
            if idx not in [1, 2, 4]:
                # overlay display region
                dr.set_active(False)

    def set_shader_input(self, *args):
        """ This is a shortcut for setting shader inputs on the buffer """
        self.get_node().set_shader_input(*args)

    def set_shader(self, shader):
        """ This is a shortcut for setting shaders to the buffer """
        self.get_node().set_shader(shader)

    def get_target(self, target):
        """ Returns the texture handle for the given target """
        return self._targets[target]

    def get_color_texture(self):
        """ Returns the handle to the color texture """
        return self.get_texture(RenderTargetType.COLOR)

    def get_depth_texture(self):
        """ Returns the handle to the depth texture """
        return self.get_texture(RenderTargetType.DEPTH)

    def get_internal_buffer(self):
        """ Returns the internal buffer object """
        return self._internal_buffer

    def get_internal_region(self):
        """ Returns the internal display region, this can be used to set
        custom sort values."""
        return self._internal_buffer.get_display_region(0)

    def get_aux_texture(self, index=0):
        """ Returns the n-th aux texture, starting at 0 """
        assert(index < 4)
        aux_textures = [
            RenderTargetType.AUX_0,
            RenderTargetType.AUX_1,
            RenderTargetType.AUX_2,
            RenderTargetType.AUX_3
        ]
        return self.get_texture(aux_textures[index])

    def set_source(self, source_cam, source_win, region=None):
        """ Sets source window and camera. When region is None, it will
        be set automatically (highly recommended) """
        self._source_cam = source_cam
        self._source_window = source_win
        self._region = region

    def set_bind_mode_layered(self, layered=True):
        """ When rendering layered, you have to call this. This
        sets the internal bind mode for the RenderBuffer. When not using
        layered bind mode, the rendering might get very slow. """
        if layered:
            self._bind_mode = GraphicsOutput.RTM_bind_layered
        else:
            self._bind_mode = GraphicsOutput.RTM_bind_or_copy

    def add_render_texture(self, target_type):
        """ Lower level function to add a new target. target_type should be
        a RenderTargetType """
        if target_type in self._targets:
            self.error("You cannot add another type of", target_type)
            return False

        self.debug("Adding render texture: ", target_type)
        self._targets[target_type] = Texture(self._name + "-" +
                                             target_type[0].upper() +
                                             target_type[1:])

    def add_color_texture(self):
        """ Adds a color target """
        return self.add_render_texture(RenderTargetType.COLOR)

    def add_depth_texture(self):
        """ Adds a depth target """
        return self.add_render_texture(RenderTargetType.DEPTH)

    def add_color_and_depth(self):
        """ Adds a color and depth target """
        self.add_color_texture()
        self.add_depth_texture()

    def add_aux_textures(self, num):
        """ Adds n aux textures. num should be between 1 and 4 """
        assert(num > 0 and num <= 4)
        targets = [
            RenderTargetType.AUX_0,
            RenderTargetType.AUX_1,
            RenderTargetType.AUX_2,
            RenderTargetType.AUX_3,
        ]

        for i in range(num):
            self.add_render_texture(targets[i])

    def add_aux_texture(self):
        """ Adds a single aux texture """
        self.add_aux_textures(1)

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

    def get_region(self):
        """ Returns the display region of this target. You can use
        this to set custom clears """
        return self._region

    def prepare_scene_render(self, early_z=False, early_z_cam=None):
        """ Renders the scene of the source camera to the buffer. See the
        documentation of this class for further information """

        self.debug("Preparing scene render")

        # Init buffer object
        self._create_buffer()

        # Prepare initial state
        cs = NodePath("InitialStateDummy")
        cs.set_state(self._source_cam.node().get_initial_state())
        if self.has_target(RenderTargetType.AUX_0):
            cs.set_attrib(AuxBitplaneAttrib.make(self._aux_bits), 20)

        cs.set_attrib(StencilAttrib.make_off(), 20)

        if not self._enable_transparency:
            cs.set_attrib(
                TransparencyAttrib.make(TransparencyAttrib.M_none), 100)

        if not self._write_color:
            cs.set_attrib(ColorWriteAttrib.make(ColorWriteAttrib.C_off), 100)

        self._source_cam.node().set_initial_state(cs.get_state())

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

        # Set clears
        buffer_region = self._internal_buffer.get_display_region(0)
        self._correct_clears()

        buffer_region.set_clear_stencil_active(False)

        # Set aux clears
        target_check = [
            (RenderTargetType.AUX_0, GraphicsOutput.RTP_aux_rgba_0),
            (RenderTargetType.AUX_1, GraphicsOutput.RTP_aux_rgba_1),
            (RenderTargetType.AUX_2, GraphicsOutput.RTP_aux_rgba_2),
            (RenderTargetType.AUX_3, GraphicsOutput.RTP_aux_rgba_3),
        ]
        for target, targetBindPos in target_check:
            if self.has_target(target):
                buffer_region.set_clear_active(targetBindPos, 1)
                buffer_region.set_clear_value(
                    targetBindPos, Vec4(0.5, 0.5, 1.0, 0.0))

        self._region.disable_clears()

        buffer_region.set_camera(self._source_cam)
        buffer_region.set_active(1)

        if early_z:
            buffer_region.set_clear_depth_active(False)
        buffer_region.set_sort(20)

        if early_z:
            self._early_z_region.disable_clears()
            self._early_z_region.set_clear_depth_active(True)
            self._early_z_region.set_active(1)

        self._set_size_shader_input()

        self._active = True
        self._register_buffer()

    def prepare_offscreen_buffer(self):
        """ Creates an offscreen buffer for this target """

        self.debug("Preparing offscreen buffer")

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

        buffer_cam.set_initial_state(initial_state.get_state())

        self._camera = self._node.attach_new_node(buffer_cam)

        buffer_region = self._internal_buffer.get_display_region(0)
        buffer_region.set_camera(self._camera)
        buffer_region.set_active(1)
        self._set_size_shader_input()

        self._active = True
        self._register_buffer()

    def set_active(self, active):
        """ You can enable / disable the buffer with this. When disabled,
        shaders on this buffer aren't executed """
        if self._active is not active:
            self._internal_buffer.get_display_region(
                0).set_active(active)
            # self._region.set_active(active)
            self._active = active

    def is_active(self):
        """ Returns Whether the buffer is active """
        return self._active

    def get_quad(self):
        """ Returns the quad-node path. You can use this to set attributes on it """
        return self._quad

    def get_node(self):
        """ Returns the buffer top node path, where the quad and camera is parented
        to """
        return self._node

    def get_texture(self, target):
        """ Returns the texture assigned to a target. The target should be a
        RenderTargetType """
        if target not in self._targets:
            self.error(
                "The target", target, "isn't bound to this RenderTarget!")
            return

        return self.get_target(target)

    def set_clear_depth(self, clear=True, force=False):
        """ Adds a depth clear """
        self._internal_buffer.set_clear_depth_active(clear)
        if clear:
            self._internal_buffer.set_clear_depth(1.0)

        if force:
            self.get_internal_region().set_clear_depth(clear)

    def set_clear_color(self, clear=True, color=None):
        """ Adds a color clear """
        self.get_internal_region().set_clear_color_active(clear)
        self._internal_buffer.set_clear_color_active(clear)

        if clear:
            if color is None:
                color = Vec4(1, 0, 1, 1)
            self._internal_buffer.set_clear_color(color)
            # self.get_internal_region().set_clear_color(color)

    def remove_quad(self):
        """ Removes the fullscren quad after creation, this might be required
        when rendering to a scene which is not the main scene """
        self.get_quad().node().remove_all_children()

    def is_active(self):
        """ Returns Whether this buffer is currently active """
        return self._active

    def delete_buffer(self):
        """ Deletes this buffer, restoring the previous state """
        # MemoryMonitor.unregister_render_target(self._name, self)
        self._internal_buffer.clear_render_textures()
        self._engine.remove_window(self._internal_buffer)
        self._active = False
        BufferViewer.unregister_entry(self)

        if self._create_overlay_quad:
            self._quad.remove_node()

        for target in RenderTargetType.ALL:
            if self.has_target(target):
                tex = self.get_target(target)

                # TODO: Doesn'T work with scattering yet
                # tex.release_all()

    def _make_fullscreen_quad(self):
        """ Create a quad which fills the whole screen """
        cm = CardMaker("BufferQuad")
        cm.set_frame_fullscreen_quad()
        quad = NodePath(cm.generate())

        quad.set_depth_test(False)
        quad.set_depth_write(False)
        quad.set_attrib(TransparencyAttrib.make(TransparencyAttrib.M_none), 1000)
        quad.set_color(Vec4(1, 0.5, 0.5, 1))

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
            dr = self._source_window.get_display_region(i)
            drcam = dr.get_camera()
            if (drcam == self._source_cam):
                return dr
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
        """ Internal method to register the buffer at the buffer viewer """
        BufferViewer.register_entry(self)

    def _create_buffer(self):
        """ Internal method to create the buffer object """
        self._width = Globals.resolution.x if self._width < 1 else self._width
        self._height = Globals.resolution.y if self._height < 1 else self._height

        self.debug("Creating buffer")

        if not self._create():
            self.error("Failed to create buffer!")
            return False

        if self._region is None:
            self._region = self._internal_buffer.make_display_region()

    def _create(self):
        """ Attempts to create this buffer """

        # if len(self._targets.keys()) < 1:
            # self.error("no attachments!")

        color_is_float = self._color_bits >= 16
        aux_is_float = self._aux_bits >= 16

        self.debug("Bitcount: color=" + str(self._color_bits) +
                   "; aux=" + str(self._aux_bits) + "; depth=" + str(self._depth_bits))

        # set wrap modes for color + auxtextures,
        # also set correct formats:
        # panda doesnt use sized formats automatically, this
        # gives problems when using imageLoad / imageStore
        prepare = [
            RenderTargetType.COLOR,
            RenderTargetType.AUX_0,
            RenderTargetType.AUX_1,
            RenderTargetType.AUX_2,
            RenderTargetType.AUX_3,
        ]

        for target in prepare:
            if not self.has_target(target):
                continue
            handle = self.get_target(target)
            handle.set_wrap_u(Texture.WMClamp)
            handle.set_wrap_v(Texture.WMClamp)
            handle.set_wrap_w(Texture.WMClamp)
            handle.set_minfilter(Texture.FTLinear)
            handle.set_magfilter(Texture.FTLinear)
            handle.set_anisotropic_degree(0)

            handle.set_x_size(self._width)
            handle.set_y_size(self._height)

            if target == RenderTargetType.COLOR:
                if color_is_float:
                    handle.set_component_type(Texture.TFloat)

                if self._color_bits == 8:
                    if self._have_color_alpha:
                        handle.set_format(Texture.FRgba8)
                    else:
                        handle.set_format(Texture.FRgb8)

                elif self._color_bits == 16:
                    if self._have_color_alpha:
                        handle.set_format(Texture.FRgba16)
                    else:
                        handle.set_format(Texture.FRgb16)

                elif self._color_bits == 32:
                    if self._have_color_alpha:
                        handle.set_format(Texture.FRgba32)
                    else:
                        handle.set_format(Texture.FRgb32)
            else:
                if aux_is_float:
                    handle.set_component_type(Texture.TFloat)

                if self._aux_bits == 8:
                    handle.set_format(Texture.FRgba8)
                elif self._aux_bits == 16:
                    handle.set_format(Texture.FRgba16)
                elif self._aux_bits == 32:
                    handle.set_format(Texture.FRgba32)

            if self._layers > 1:
                if self._use_texture_arrays:
                    handle.setup2dTextureArray(self._layers)
                else:
                    handle.setup3dTexture(self._layers)

        # set layers for depth texture
        if self._layers > 1 and self.has_target(RenderTargetType.DEPTH):
            if self._use_texture_arrays:
                self.get_target(RenderTargetType.DEPTH).setup2dTextureArray(
                    self._layers)
            else:
                self.get_target(RenderTargetType.DEPTH).setup3dTexture(
                    self._layers)

        # Create buffer descriptors
        window_props = WindowProperties.size(self._width, self._height)
        buffer_props = FrameBufferProperties()

        # Set color and alpha bits
        if self.has_target(RenderTargetType.COLOR):
            buffer_props.set_rgba_bits(self._color_bits, self._color_bits,
                                       self._color_bits, self._color_bits
                                       if self._have_color_alpha else 0)
            if color_is_float:
                buffer_props.set_float_color(True)

        # Set aux bits
        if self.has_target(RenderTargetType.AUX_0) and aux_is_float:
            # FRAMEBUFFER INCOMPLETE when using this to render to a 3d texture
            # buffer_props.set_aux_float(True)
            pass

        # Set depth bits and depth texture format
        if self.has_target(RenderTargetType.DEPTH):
            depth_target = self.get_target(RenderTargetType.DEPTH)

            buffer_props.set_depth_bits(self._depth_bits)
            buffer_props.set_float_depth(True)

            if self._depth_bits != 32:
                self.error("You cannot request a non-32bit float depth buffer!"
                           " Requesting a non-float depth buffer instead!")
                buffer_props.set_float_depth(False)

            if self._depth_bits == 16:
                depth_target.set_format(Texture.FDepthComponent16)
            if self._depth_bits == 24:
                depth_target.set_format(Texture.FDepthComponent24)
            elif self._depth_bits == 32:
                depth_target.set_format(Texture.FDepthComponent32)

            depth_target.set_x_size(self._width)
            depth_target.set_y_size(self._height)

        # We need no stencil (not supported yet)
        buffer_props.set_stencil_bits(0)

        num_auxtex = 0

        # Python really needs switch()
        # FIXME: Why is it 2 when only 1 AUX texture is attached?!
        if self.has_target(RenderTargetType.AUX_3):
            num_auxtex = 3
        elif self.has_target(RenderTargetType.AUX_2):
            num_auxtex = 3
        elif self.has_target(RenderTargetType.AUX_1):
            num_auxtex = 2
        elif self.has_target(RenderTargetType.AUX_0):
            num_auxtex = 1

        # Add aux textures (either 8 or 16 bit)
        if aux_is_float:
            buffer_props.set_aux_hrgba(num_auxtex)
        else:
            buffer_props.set_aux_rgba(num_auxtex)

        buffer_props.set_multisamples(self._multisamples)

        # Register the target for the memory monitoring
        # MemoryMonitor.add_render_target(self._name, self)

        # Create internal graphics output
        self._internal_buffer = self._engine.make_output(
            self._source_window.get_pipe(), self._name, 1,
            buffer_props, window_props,
            GraphicsPipe.BFRefuseWindow,
            self._source_window.get_gsg(), self._source_window)

        if self._internal_buffer is None:
            self.error("Failed to create buffer :(")
            return False

        # Add render targets
        if self.has_target(RenderTargetType.DEPTH):
            self._internal_buffer.add_render_texture(
                self.get_target(RenderTargetType.DEPTH), self._bind_mode,
                GraphicsOutput.RTPDepth)

        if self.has_target(RenderTargetType.COLOR):
            self._internal_buffer.add_render_texture(
                self.get_target(RenderTargetType.COLOR), self._bind_mode,
                GraphicsOutput.RTPColor)

        modes = [
            (RenderTargetType.AUX_0, GraphicsOutput.RTPAuxHrgba0,
             GraphicsOutput.RTPAuxRgba0),
            (RenderTargetType.AUX_1, GraphicsOutput.RTPAuxHrgba1,
             GraphicsOutput.RTPAuxRgba1),
            (RenderTargetType.AUX_2, GraphicsOutput.RTPAuxHrgba2,
             GraphicsOutput.RTPAuxRgba2),
            (RenderTargetType.AUX_3, GraphicsOutput.RTPAuxHrgba3,
             GraphicsOutput.RTPAuxRgba3),
        ]

        for target, float_mode, normal_mode in modes:
            if self.has_target(target):
                self._internal_buffer.add_render_texture(
                    self.get_target(target), self._bind_mode,
                    float_mode if aux_is_float else normal_mode)

        # Increment global sort counter
        RenderTarget._NUM_BUFFERS_ALLOCATED += 1
        self._sort = -300 + RenderTarget._NUM_BUFFERS_ALLOCATED * 10

        self._internal_buffer.set_sort(self._sort)
        self._internal_buffer.disable_clears()
        self._internal_buffer.get_display_region(0).disable_clears()

        for i in xrange(16):
            self._internal_buffer.set_clear_active(i, False)
            self._internal_buffer.get_display_region(0).set_clear_active(i, False)

        self._internal_buffer.set_clear_stencil_active(False)

        if self.has_target(RenderTargetType.DEPTH):
            depth_target = self.get_target(RenderTargetType.DEPTH)

            if self._depth_bits == 16:
                depth_target.set_format(Texture.FDepthComponent16)
            elif self._depth_bits == 24:
                depth_target.set_format(Texture.FDepthComponent24)
            elif self._depth_bits == 32:
                depth_target.set_format(Texture.FDepthComponent32)
        return True

    def __repr__(self):
        """ Returns a representative string of this instance """
        return "RenderTarget('" + self._name + "')"
