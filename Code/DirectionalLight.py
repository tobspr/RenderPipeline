
from Light import Light
from DebugObject import DebugObject
from panda3d.core import OmniBoundingVolume
from LightType import LightType
from NoSenseException import NoSenseException


class DirectionalLight(Light, DebugObject):

    """ This light type simulates sunlight, or any other very
    big light source. When shadows are enabled, PSSM is used.
    A directional light has no position or radius, only a direction. 
    Therefore, setRadius and setPos have no effect. 

    DirectionalLight do not support debug nodes (yet). Also PSSM
    is not implemented (yet).

    """

    def __init__(self):
        """ Constructs a new directional light. You have to set a
        direction for this light to work properly"""
        Light.__init__(self)
        DebugObject.__init__(self, "DirectionalLight")
        self.typeName = "DirectionalLight"

        # A directional light is always visible
        self.bounds = OmniBoundingVolume()

    def _computeLightMat(self):
        """ Todo """

    def _getLightType(self):
        """ Internal method to fetch the type of this light, used by Light """
        return LightType.Directional

    def _computeLightBounds(self):
        """ This does nothing, we only have a OmniBoundingVolume() and therefore
        don't have to recompute our lighting bounds every time the application 
        changes something """

    def setRadius(self, x):
        """ This makes no sense, as a directional light has no radius """
        raise NoSenseException("DirectionalLight has no radius")

    def setPos(self, x):
        """ This makes no sense, as a directional light has no position """
        raise NoSenseException("DirectionalLight has no position")

    def _computeAdditionalData(self):
        """ The directional light has no additional data (yet) to pass to the
        shaders """

    def _updateDebugNode(self):
        """ Debug nodes are not supported by directional lights (yet), so this
        does nothing """

    def _initShadowSources(self):
        """ Shadows aren't supported for directional lights (yet), so this does
        nothing """

    def _updateShadowSources(self):
        """ Shadows aren't supported for directional lights (yet), so this does
        nothing """

    def __repr__(self):
        """ Generates a representative string for this object """
        return "DirectionalLight[pos=" + str(self.position) + ", radius=" + str(self.radius) + ",dir=" + str(self.direction) + "]"
