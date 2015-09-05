

from Light import Light

class PointLight(Light):

    """ Point light """

    def __init__(self):
        Light.__init__(self)
        self.radius = 1.0
        self.innerRadius = 1.0

    def setRadius(self, radius):
        """ Sets the light radius """
        self.radius = radius
        self._markDirty()

    def setInnerRadius(self, innerRadius):
        """ Sets the light inner radius """
        self.innerRadius = innerRadius
        self._markDirty()

    def getLightType(self):
        """ Returns the type of this light """
        return self.LTPointLight
