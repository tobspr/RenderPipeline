
def __init__(self, light_type):
    self._light_type = light_type
    self._dirty = False
    self._slot = -1
    self._position = Vec3(0)
    self._color = Vec3(1)
    self._ies_profile = -1

def write_to_command(self, cmd):
    cmd.push_int(self._slot)
    cmd.push_int(self._light_type)
    cmd.push_int(self._ies_profile)
    cmd.push_vec3(self._position)
    cmd.push_vec3(self._color)

def mark_dirty(self):
    self._dirty = True

def unset_dirty_flag(self):
    self._dirty = False

def is_dirty(self):
    return self._dirty

def set_pos(self, *args):
    self._position = Vec3(*args)
    self.mark_dirty()

def set_color(self, *args):
    self._color = Vec3(*args)
    self.mark_dirty()

def has_slot(self):
    return self._slot >= 0

def remove_slot(self):
    self._slot = -1

def assign_slot(self, slot):
    self._slot = slot

def get_light_type(self):
    return self._light_type

def get_slot(self):
    return self._slot

def set_ies_profile(self, profile):
    self._ies_profile = profile

def set_casts_shadows(self, flag=True):
    print("set_casts_shadows: TODO")
