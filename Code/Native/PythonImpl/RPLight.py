from __future__ import print_function

from panda3d.core import Vec3

class RPLight(object):

    LT_empty = 0
    LT_point_light = 1
    LT_spot_light = 2

    def __init__(self, light_type):
        self._light_type = light_type
        self._needs_update = False
        self._casts_shadows = False
        self._slot = -1
        self._position = Vec3(0)
        self._color = Vec3(1)
        self._ies_profile = -1
        self._source_resolution = 512
        self._near_plane = 0.1
        self._lumens = 20
        self._shadow_sources = []

    def get_num_shadow_sources(self):
        return len(self._shadow_sources)

    def get_shadow_source(self, index):
        return self._shadow_sources[index]

    def clear_shadow_sources(self):
        self._shadow_sources = []

    def set_needs_update(self, flag):
        self._needs_update = flag

    def get_needs_update(self):
        return self._needs_update

    def has_slot(self):
        return self._slot >= 0

    def get_slot(self):
        return self._slot

    def remove_slot(self):
        self._slot = -1

    def assign_slot(self, slot):
        self._slot = slot

    def invalidate_shadows(self):
        for source in self._shadow_sources:
            source.set_needs_update(true)

    def set_pos(self, *args):
        self._position = Vec3(*args)
        self.set_needs_update(True)
        self.invalidate_shadows()

    def get_pos(self):
        return self._position

    pos = property(get_pos, set_pos)

    def set_color(self, *args):
        self._color = Vec3(*args)
        self._color /= (0.2126 * self._color.x +
                        0.7152 * self._color.y +
                        0.0722 * self._color.z)
        self.set_needs_update(True)

    def get_color(self):
        return self._color

    color = property(get_color, set_color)

    def set_lumens(self, lumens):
        self._lumens = lumens

    def get_lumens(self):
        return self._lumens

    lumens = property(get_lumens, set_lumens)

    def get_light_type(self):
        return self._light_type

    light_type = property(get_light_type)

    def set_casts_shadows(self, flag):
        if self.has_slot():
            print("Light is already attached!")
            return
        self._casts_shadows = flag

    def get_casts_shadows(self):
        return self._casts_shadows

    casts_shadows = property(get_casts_shadows, set_casts_shadows)

    def set_shadow_map_resolution(self, resolution):
        self._source_resolution = resolution
        self.invalidate_shadows()

    def get_shadow_map_resolution(self):
        return self._source_resolution

    shadow_map_resolution = property(get_shadow_map_resolution, set_shadow_map_resolution)

    def set_ies_profile(self, profile):
        self._ies_profile = profile
        set_needs_update(True)

    def get_ies_profile(self):
        return self._ies_profile


    def has_ies_profile(self):
        return self._ies_profile >= 0

    def clear_ies_profile(self):
        self.set_ies_profile(-1)

    ies_profile = property(get_ies_profile, set_ies_profile)

    def set_near_plane(self, near_plane):
        self._near_plane = near_plane
        self.invalidate_shadows()

    def get_near_plane(self):
        return self._near_plane

    near_plane = property(get_near_plane, set_near_plane)


    def write_to_command(self, cmd):
        cmd.push_int(self._light_type)
        cmd.push_int(self._ies_profile)

        if self._casts_shadows:
            cmd.push_int(self._shadow_sources[0].get_slot())
        else:
            cmd.push_int(-1)

        cmd.push_vec3(self._position)
        cmd.push_vec3(self._color * self._lumens)
