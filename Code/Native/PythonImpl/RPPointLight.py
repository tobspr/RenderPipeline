
from panda3d.core import Vec3

from .RPLight import RPLight
from .ShadowSource import ShadowSource

class RPPointLight(RPLight):

    def __init__(self):
        RPLight.__init__(self, RPLight.LT_point_light)
        self._radius = 10.0
        self._inner_radius = 0.0

    def write_to_command(self, cmd):
        RPLight.write_to_command(self, cmd)
        cmd.push_float(self._radius)
        cmd.push_float(self._inner_radius)

    def set_radius(self, radius):
        self._radius = radius
        self.set_needs_update(True)
        self.invalidate_shadows()

    def get_radius(self):
        return self._radius

    radius = property(get_radius, set_radius)

    def set_inner_radius(self, inner_radius):
        self._inner_radius = inner_radius
        self.set_needs_update(True)

    def get_inner_radius(self):
        return self._inner_radius

    inner_radius = property(get_inner_radius, set_inner_radius)

    def init_shadow_sources(self):
        for i in range(6):
            self._shadow_sources.append(ShadowSource())
        
    def update_shadow_Sources(self):
        directions = [
            Vec3( 1,  0,  0),
            Vec3(-1,  0,  0),
            Vec3( 0,  1,  0),
            Vec3( 0, -1,  0),
            Vec3( 0,  0,  1),
            Vec3( 0,  0, -1)
        ]

        fov = 90.0 + 3.0
        for i, source in enumerate(self._shadow_sources):
            source.set_resolution(self.get_shadow_map_resolution())
            source.set_perspective_lens(fov, self._near_plane, self._radius,
                                        self._position, directions[i])
