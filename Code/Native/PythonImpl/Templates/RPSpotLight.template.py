
def __init__(self):
    RPLight.__init__(self, RPLight.LT_spot_light)
    self._radius = 10.0
    self._fov = 45.0
    self._direction = Vec3(0, 0, -1)

def write_to_command(self, cmd):
    RPLight.write_to_command(self, cmd)
    cmd.push_float(self._radius)
    cmd.push_float(self._fov / 180.0 * math.pi)
    cmd.push_vec3(self._direction)

def set_radius(self, radius):
    self._radius = radius
    self.mark_dirty()

def set_fov(self, fov):
    self._fov = fov
    self.mark_dirty()

def set_direction(self, *args):
    self._direction = Vec3(*args)
    self._direction.normalize()
    self.mark_dirty()

def look_at(self, *args):
    vec = Vec3(*args) - self._position
    self.set_direction(vec)


