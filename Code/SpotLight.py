
import math

from panda3d.core import NodePath, Vec4, Vec3, BoundingSphere, Point3
from panda3d.core import OmniBoundingVolume, Vec2

from Light import Light
from DebugObject import DebugObject
from LightType import LightType
from ShadowSource import ShadowSource
from Globals import Globals

class SpotLight(Light, DebugObject):

    """ This light type simulates a SpotLight. It has a position
    and an orientation. """

    def __init__(self):
        """ Creates a new spot light. """
        Light.__init__(self)
        DebugObject.__init__(self, "SpotLight")
        self.typeName = "SpotLight"

        self.nearPlane = 0.5
        self.radius = 30.0
        self.spotSize = Vec2(30, 30)

    def _getLightType(self):
        """ Internal method to fetch the type of this light, used by Light """
        return LightType.Spot

    def _computeLightBounds(self):
        """ Recomputes the bounds of this light. For a SpotLight, we for now
        use a simple BoundingSphere """
        self.bounds = BoundingSphere(Point3(self.position), self.radius * 2.0)

    def _computeAdditionalData(self):
        """ SpotLight does not need to store additional data """

    def setNearFar(self, near, far):
        """ Sets the near and far plane of the spotlight """
        self.nearPlane = near
        self.radius = far

    def _updateDebugNode(self):
        """ Internal method to generate new debug geometry. """
        raise NotImplementedError()

    def _initShadowSources(self):
        """ Internal method to init the shadow sources """
        source = ShadowSource()
        source.setupPerspectiveLens(
            self.nearPlane, self.radius, (self.spotSize.x, self.spotSize.y))
        source.setResolution(self.shadowResolution)
        self._addShadowSource(source)

    def _updateShadowSources(self):
        """ Recomputes the position of the shadow source """

        self.shadowSources[0].setPos(self.position)
        self.shadowSources[0].lookAt(self.position + self.direction)

    def __repr__(self):
        """ Generates a string representation of this instance """
        return "SpotLight[id=" + str(self.structElementID) + "]"
