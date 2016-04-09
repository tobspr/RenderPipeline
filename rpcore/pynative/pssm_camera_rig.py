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

from panda3d.core import PTALVecBase2f, PTALMatrix4f, Vec2, OrthographicLens
from panda3d.core import Camera, NodePath, Mat4

class PSSMCameraRig(object):

    """ PSSM is not really supported in python yet (too slow), so this is a stub,
    supporting only one cascade """

    def __init__(self, num_splits):
        self._split_count = num_splits
        self._mvps = PTALMatrix4f.empty_array(num_splits)
        self._nearfar = PTALVecBase2f.empty_array(num_splits)
        for i in range(num_splits):
            self._nearfar[i] = Vec2(20, 1000)
            mat = Mat4()
            mat.fill(0)
            self._mvps[i] = mat
        self._lens = OrthographicLens()
        self._lens.set_near_far(20, 1000)
        self._lens.set_film_size(100, 100)
        self._camera = Camera("PSSMDummy", self._lens)
        self._cam_node = NodePath(self._camera)
        self._parent = None

    def update(self, cam_node, light_vector):
        cam_pos = cam_node.get_pos()
        self._cam_node.set_pos(cam_pos + light_vector * 500)
        self._cam_node.look_at(cam_pos)

        transform = self._parent.get_transform(self._cam_node).get_mat()
        self._mvps[0] = transform * self._lens.get_projection_mat()

    def get_camera(self, index): # pylint: disable=W0613
        return self._cam_node

    def reparent_to(self, parent):
        self._cam_node.reparent_to(parent)
        self._parent = parent

    def get_mvp_array(self):
        return self._mvps

    def get_nearfar_array(self):
        return self._nearfar

    # Stubs
    def _stub(self, *args, **kwargs):
        pass

    set_pssm_distance = _stub
    set_sun_distance = _stub
    set_resolution = _stub
    set_use_stable_csm = _stub
    set_logarithmic_factor = _stub
    set_border_bias = _stub
    set_use_fixed_film_size = _stub
    reset_film_size_cache = _stub
