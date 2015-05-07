
from panda3d.core import OmniBoundingVolume, Vec3, Vec2, Point3, Point2

import math

from Light import Light
from DebugObject import DebugObject
from LightType import LightType
from NoSenseException import NoSenseException
from ShadowSource import ShadowSource
from Globals import Globals

class GIHelperLight(Light, DebugObject):

    """ This light type is used by the Global Illumination. It shades the voxel
    grid from the sun position. During voxelization this lights shadowmap is
    used to shade the pixel. The light is not visible in the main scene
    """

    def __init__(self):
        """ Constructs a new directional light. You have to set a
        direction for this light to work properly"""
        Light.__init__(self)
        DebugObject.__init__(self, "GIHelperLight")
        self.typeName = "GIHelperLight"
        self.targetLight = None
        self.filmSize = 50
        self.bounds = OmniBoundingVolume()

    def setFilmSize(self, size):
        """ Sets the film size of the lights shadow lens. Has no effect after
        setCastsShadows was called. """
        self.filmSize = size

    def setTargetLight(self, target):
        """ Sets the target light. This light will use the same direction as the
        target light. """
        self.targetLight = target

    def _computeLightMat(self):
        """ Todo """

    def _getLightType(self):
        """ Internal method to fetch the type of this light, used by Light """
        return LightType.NoType

    def _computeLightBounds(self):
        """ This does nothing, we only have a OmniBoundingVolume() and therefore
        don't have to recompute our lighting bounds every time the application 
        changes something """

    def setRadius(self, x):
        """ This makes no sense, as a directional light has no radius """
        raise NoSenseException("GIHelperLight has no radius")

    def needsUpdate(self):
        """ The helper light should get updated each frame to reposition the
        shadow sources """
        return True

    def _computeAdditionalData(self):
        """ This light has no additional data (yet) to pass to the
        shaders """

    def _updateDebugNode(self):
        """ Debug nodes are not supported by helper lights, this does nothing """

    def _initShadowSources(self):
        """ Creates the shadow sources used for shadowing """

        source = ShadowSource()
        source.setupOrtographicLens(
            5.0, 2000.0, (self.filmSize, self.filmSize))
        source.setResolution(self.shadowResolution)
        self._addShadowSource(source)

    def _updateShadowSources(self):
        """ Updates the PSSM Frustum and all PSSM Splits """

        self.shadowSources[0].setPos(self.position + self.direction * 500.0)
        self.shadowSources[0].lookAt(self.position)
        self.shadowSources[0].invalidate()

    def __repr__(self):
        """ Generates a representative string for this object """
        return "GIHelperLight[pos=" + str(self.position) + ", dir=" + str(self.direction) + "]"
