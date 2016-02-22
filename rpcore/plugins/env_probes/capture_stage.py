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
from rplibs.six.moves import range

from panda3d.core import Camera, PerspectiveLens, Vec4, NodePath, Vec3
from panda3d.core import PTAInt

from rpcore.globals import Globals
from rpcore.render_stage import RenderStage

class EnvironmentCaptureStage(RenderStage):

    """ This stage renders the scene to a cubemap """

    required_inputs = ["DefaultEnvmap"]
    required_pipes = []

    def __init__(self, pipeline):
        RenderStage.__init__(self, "EnvironmentCaptureStage", pipeline)
        self.resolution = 512
        self.regions = []
        self.cameras = []
        self.rig_node = Globals.render.attach_new_node("EnvmapCamRig")
        self.pta_index = PTAInt.empty_array(1)
        self.storage_tex = None

    def create(self):
        self._target = self.make_target("CaptureScene")
        self._target.set_source(None, Globals.base.win)
        self._target.size = (self.resolution * 6, self.resolution)
        self._target.add_color_texture(bits=16)
        # self._target.add_depth_texture(bits=32)
        self._target.has_color_alpha = True
        self._target.create_overlay_quad = False
        self._target.prepare_scene_render()

        # Remove all unused display regions
        internal_buffer = self._target.get_internal_buffer()
        internal_buffer.remove_all_display_regions()
        internal_buffer.get_display_region(0).set_active(False)

        internal_buffer.set_clear_color_active(True)
        internal_buffer.set_clear_depth_active(True)
        internal_buffer.set_clear_color(Vec4(0))
        internal_buffer.set_clear_depth(1.0)

        directions = (Vec3(1, 0, 0), Vec3(-1, 0, 0), Vec3(0, 1, 0),
                      Vec3(0, -1, 0), Vec3(0, 0, 1), Vec3(0, 0, -1))

        # Prepare the display regions
        for i in range(6):
            region = internal_buffer.make_display_region(
                i / 6, i / 6 + 1 / 6, 0, 1)
            # region.set_clear_depth(1)
            region.set_clear_color_active(False)
            region.set_clear_depth_active(False)
            region.set_sort(25 + i)
            region.set_active(True)

            lens = PerspectiveLens()
            lens.set_fov(90)
            lens.set_near_far(0.001, 1.0)
            camera = Camera("EnvmapCam-" + str(i), lens)
            camera_np = self.rig_node.attach_new_node(camera)
            camera_np.look_at(camera_np, directions[i])
            region.set_camera(camera_np)
            self.regions.append(region)
            self.cameras.append(camera_np)

        self.cameras[0].set_r(90)
        self.cameras[1].set_r(-90)
        self.cameras[3].set_r(180)
        self.cameras[5].set_r(180)

        # Register cameras
        for camera_np in self.cameras:
            self._pipeline.tag_mgr.register_envmap_camera(camera_np.node())

        self._target_store = self.make_target("StoreCubemap")
        self._target_store.size = (self.resolution * 6, self.resolution)
        self._target_store.prepare_offscreen_buffer()
        self._target_store.set_shader_input("SourceTex", self._target["color"])
        self._target_store.set_shader_input("DestTex", self.storage_tex)
        self._target_store.set_shader_input("currentIndex", self.pta_index)

        # Generate the targets which filter the cubemap
        self.filter_targets = []
        mip = 0
        size = self.resolution
        while size > 1:
            size = size // 2
            mip += 1
            target = self.make_target("FilterCubemap:{}".format(mip))
            target.set_size(size * 6, size)
            target.prepare_offscreen_buffer()
            target.set_shader_input("currentIndex", self.pta_index)
            target.set_shader_input("currentMip", mip)
            target.set_shader_input("SourceTex", self.storage_tex)
            target.set_shader_input("DestTex", self.storage_tex, False, True, -1, mip, 0)
            self.filter_targets.append(target)

    def render_probe(self, probe):
        if probe is None:
            self.warn("TODO: Disable all regions")
        else:
            self.rig_node.set_mat(probe.matrix)
        self.pta_index[0] = probe.index

    def set_shader_input(self, *args):
        Globals.render.set_shader_input(*args)

    def set_shaders(self):
        self._target_store.set_shader(self.load_plugin_shader("store_cubemap.frag.glsl"))
        filter_shader = self.load_plugin_shader("filter_cubemap.frag.glsl")
        for target in self.filter_targets:
            target.set_shader(filter_shader)
