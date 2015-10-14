

from .Light import Light


class PointLight(Light):

    """ Point light """

    def __init__(self):
        Light.__init__(self)
        self._radius = 1.0
        self._inner_radius = 1.0

    def set_radius(self, radius):
        """ Sets the light radius """
        self._radius = radius
        self._mark_dirty()

    def set_inner_radius(self, inner_radius):
        """ Sets the light inner radius """
        self._inner_radius = inner_radius
        self._mark_dirty()

    def get_light_type(self):
        """ Returns the type of this light """
        return self.LT_POINT_LIGHT

    def add_to_stream(self, command):
        Light.add_to_stream(self, command)
        command.push_float(self._radius)
        command.push_float(self._inner_radius)
