
from panda3d.core import Mat4, PerspectiveLens, LVector3, LVecBase2i, LVecBase2f

class ShadowSource(object):

    def __init__(self):
        self._slot = -1
        self._needs_update = True
        self._resolution = 512
        self._mvp = 0.0
        self._region = LVecBase2i(-1)
        self._region_uv = LVecBase2f(0.0)

    def set_resolution(self, resolution):
        self._resolution = resolution

    def set_needs_update(self, flag):
        self._needs_update = flag

    def set_slot(self, slot):
        self._slot = slot

    def set_region(self, region, region_uv):
        self._region = region
        self._region_uv = region_uv

    def set_perspective_lens(self, fov, near_plane, far_plane, pos, direction):
        transform_mat = Mat4.translate_mat(-pos)
        temp_lens = PerspectiveLens(fov, fov)
        temp_lens.set_film_offset(0, 0)
        temp_lens.set_near_far(near_plane, far_plane)
        temp_lens.set_view_vector(direction, LVector3.up())
        self.set_matrix_lens(transform_mat * temp_lens.get_projection_mat())

    def set_matrix_lens(self, mvp):
        self._mvp = mvp
        self.set_needs_update(True)

    def has_region(self):
        return (self._region.x >= 0 and self._region.y >= 0 and
                self._region.z >= 0 and self._region.w >= 0)

    def has_slot(self):
        return self._slot >= 0

    def get_slot(self):
        return self._slot

    def get_needs_update(self):
        return self._needs_update

    def get_resolution(self):
        return self._resolution

    def get_mvp(self):
        return self._mvp

    def get_region(self):
        return self._region

    def get_uv_region(self):
        return self._region_uv

    def write_to_command(self, cmd):
        cmd.push_mat4(self._mvp)
        cmd.push_vec4(self._region_uv)
