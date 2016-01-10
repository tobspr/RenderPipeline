"""

RenderPipeline

Copyright (c) 2014-2015 tobspr <tobias.springer1@gmail.com>

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

from panda3d.core import RenderState, ColorWriteAttrib, ShaderAttrib, BitMask32

class TagStateManager(object):

    def __init__(self, main_cam_node):
        self._main_cam_node = main_cam_node
        self._shadow_cameras = set()
        self._tag_states = {}

    def get_gbuffer_mask(self):
        return BitMask32.bit(1)

    def get_shadow_mask(self):
        return BitMask32.bit(2)

    def get_voxelize_mask(self):
        return BitMask32.bit(3)

    def apply_shadow_state(self, np, shader, name, sort):
        state = RenderState.make_empty()
        state = state.set_attrib(ColorWriteAttrib.make(ColorWriteAttrib.C_off), 10000)
        state = state.set_attrib(ShaderAttrib.make(shader), sort)

        if name in self._tag_states:
            print("TagStateManager: Warning: Overiding existing state", name)
        self._tag_states[name] = state

        # Save the tag on the node path
        np.set_tag("Shadows", name)

        for cam in self._shadow_cameras:
            cam.set_tag_state(name, state)

    def cleanup_states(self):
        self._main_cam_node.node().clear_tag_states()
        for cam in self._shadow_cameras:
            cam.clear_tag_states()

    def register_shadow_camera(self, source):
        source.set_tag_state_key("Shadows")
        source.set_camera_mask(self.get_shadow_mask())
        self._shadow_cameras.add(source)

    def unregister_shadow_camera(self, source):
        self._shadow_cameras.remove(source)
