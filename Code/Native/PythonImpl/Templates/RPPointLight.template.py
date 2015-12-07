
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
    self.mark_dirty()

def set_inner_radius(self, inner_radius):
    self._inner_radius = inner_radius
    self.mark_dirty()

    