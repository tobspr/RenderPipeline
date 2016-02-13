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

from __future__ import print_function
from panda3d.core import RenderState, ColorWriteAttrib, ShaderAttrib, BitMask32

class TagStateManager(object):

    class StateContainer(object):
        def __init__(self, tag_name, mask):
            self.cameras = []
            self.tag_states = {}
            self.tag_name = tag_name
            self.mask = mask

    def __init__(self, main_cam_node):
        self._main_cam_node = main_cam_node
        self._main_cam_node.node().set_camera_mask(self.get_gbuffer_mask())
        self._shadow_container = self.StateContainer("Shadows", self.get_shadow_mask())
        self._voxelize_container = self.StateContainer("Voxelize", self.get_voxelize_mask())

    def get_gbuffer_mask(self):
        return BitMask32.bit(1)

    def get_shadow_mask(self):
        return BitMask32.bit(2)

    def get_voxelize_mask(self):
        return BitMask32.bit(3)

    def apply_shadow_state(self, np, shader, name, sort):
        self.apply_state(self._shadow_container, np, shader, name, sort)

    def apply_voxelize_state(self, np, shader, name, sort):
        self.apply_state(self._voxelize_container, np, shader, name, sort)

    def register_shadow_camera(self, source):
        self.register_camera(self._shadow_container, source)

    def unregister_shadow_camera(self, source):
        self.unregister_camera(self._shadow_container, source)

    def register_voxelize_camera(self, source):
        self.register_camera(self._voxelize_container, source)

    def unregister_voxelize_camera(self, source):
        self.unregister_camera(self._voxelize_container, source)

    def apply_state(self, container, np, shader, name, sort):
        state = RenderState.make_empty()
        state = state.set_attrib(ColorWriteAttrib.make(ColorWriteAttrib.C_off), 10000)
        state = state.set_attrib(ShaderAttrib.make(shader, sort), sort)

        container.tag_states[name] = state
        np.set_tag(container.tag_name, name)

        for camera in container.cameras:
            camera.set_tag_state(name, state)

    def cleanup_states(self):
        self._main_cam_node.node().clear_tag_states()
        self.cleanup_container_states(self._shadow_container)
        self.cleanup_container_states(self._voxelize_container)

    def cleanup_container_states(self, container):
        for camera in container.cameras:
            camera.clear_tag_states()
        container.tag_states = {}

    def register_camera(self, container, source):
        source.set_tag_state_key(container.tag_name)
        source.set_camera_mask(container.mask)
        state = RenderState.make_empty()
        state = state.set_attrib(ColorWriteAttrib.make(ColorWriteAttrib.C_off), 10000)
        source.set_initial_state(state)
        container.cameras.append(source)

    def unregister_camera(self, container, source):
        if source not in container.cameras:
            print("Could not remove source, was never attached!")
            return

        container.cameras.remove(source)
        source.clear_tag_states()
        source.set_initial_state(RenderState.make_empty())

