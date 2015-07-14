
from panda3d.core import OmniBoundingVolume, Vec3, Vec2, Point3, Point2, Mat4
from panda3d.core import Point4, Vec4

import math

from Light import Light
from DebugObject import DebugObject
from LightType import LightType
from ShadowSource import ShadowSource
from Globals import Globals

from panda3d.core import PStatCollector

pstats_PSSM = PStatCollector("App:LightManager:ProcessLights:UpdatePCSMSplits")

class DirectionalLight(Light, DebugObject):

    """ This light type simulates sunlight, or any other very big light source. 
    When shadows are enabled, PSSM is used. The directional light should be set
    far away from the scene, to simulate a sun, so very big coordinates are required
    for the directional light to behave like a directional light. 

    DirectionalLight does not support debug nodes (yet). It uses a 4-Split PSSM
    by default. The PSSM can be controlled via setPssmDistance and setPssmSplitPow. 
    See the method descriptions for more information.

    If you do not use the default camera, you should pass it to the light with
    setPssmTarget.

    """

    def __init__(self):
        """ Constructs a new directional light. """
        Light.__init__(self)
        DebugObject.__init__(self, "DirectionalLight")
        self.typeName = "DirectionalLight"

        # If you change the split count, change DIRECTIONAL_LIGHT_SPLIT_COUNTS
        # in Shader/Includes/Configuration.include aswell! This is hardcoded
        # to improve performance
        self.splitCount = 6

        self.pssmTargetCam = Globals.base.cam
        self.pssmTargetLens = Globals.base.camLens
        self.pssmFarPlane = 150
        self.pssmSplitPow = 2.0
        self.sunDistance = 700
        self.updateIndex = 0

        # A directional light is always visible
        self.bounds = OmniBoundingVolume()

    def setPssmDistance(self, far_plane):
        """ Sets the distance of the last split. After this distance, no shadow
        is visible. When setting a bigger distance, the shadows reach further but
        their quality decreases. When setting a lower distance, the shadows reach
        shorter but their qualit increases. Usually you want to find a tradeoff 
        between distance and quality."""
        self.pssmFarPlane = far_plane

    def setSunDistance(self, sun_distance):
        """ Sets the distance of the sun, relative to the origin of the scene. 
        Everything above that distance will not recieve shadows! """
        self.sunDistance = sun_distance

    def setPssmSplitPow(self, split_pow):
        """ Sets the split pow to use. A higher value means the split planes are
        distributed closer to the camera, a lower value means the split planes 
        are more uniformly distributed. Using a value of 1 will make the 
        distribution uniform """
        self.pssmSplitPow = split_pow

    def setPssmTarget(self, pssm_cam, pssm_lens):
        """ Sets the camera and lens which are used for the pssm. This is
        usually (and by default) the main camera. """
        self.pssmTargetCam = pssm_cam
        self.pssmTargetLens = pssm_lens

    def getLightType(self):
        """ Internal method to fetch the type of this light, used by Light """
        return LightType.Directional

    def _computeLightBounds(self):
        """ This does nothing, we only have a OmniBoundingVolume() and therefore
        don't have to recompute our lighting bounds every time the application 
        changes something """

    def setRadius(self, x):
        """ This makes no sense, as a directional light has no radius """
        raise Exception("DirectionalLight has no radius")

    def needsUpdate(self):
        """ Directional lights have to get updated every frame to reposition
        the PSSM frustum """
        return True

    def _updateDebugNode(self):
        """ Debug nodes are not supported by directional lights (yet), so this
        does nothing """
        raise Exception("Debug nodes are not supported by directional lights yet")

    def _initShadowSources(self):
        """ Creates the shadow sources used for shadowing """
        for i in xrange(self.splitCount):
            source = ShadowSource()
            source.setupOrtographicLens(
                -self.sunDistance, self.sunDistance, (10, 10))
            source.setResolution(self.shadowResolution)
            self._addShadowSource(source)

    def _updateShadowSources(self):
        """ Updates the PSSM Frustum and all PSSM Splits """

        mixVector = lambda p1, p2, a: ((p2*a) + (p1*(1.0-a)))


        pstats_PSSM.start()

        # Fetch camera data
        camPos = self.pssmTargetCam.getPos()

        # Compute frustum points
        nearPoint = Point3()
        farPoint = Point3()
        self.pssmTargetLens.extrude(Point2(0.0), nearPoint, farPoint)
        nearPoint = Globals.base.render.getRelativePoint(self.pssmTargetCam, nearPoint)
        farPoint = Globals.base.render.getRelativePoint(self.pssmTargetCam, farPoint)

        trNearPoint = Point3()
        trFarPoint = Point3()
        self.pssmTargetLens.extrude(Point2(1.0), trNearPoint, trFarPoint)
        trNearPoint = Globals.base.render.getRelativePoint(self.pssmTargetCam, trNearPoint)
        trFarPoint = Globals.base.render.getRelativePoint(self.pssmTargetCam, trFarPoint)

        # Position the splits
        # This is the PSSM split function, currently cubic
        splitFunc = lambda x: math.pow(float(x+0.5)/(self.splitCount+0.5), self.pssmSplitPow)
        relativeSplitSize = self.pssmFarPlane / self.pssmTargetLens.getFar()

        self.updateIndex += 1
        self.updateIndex = self.updateIndex % 2

        direction = Vec3(self.position)
        direction.normalize()

        # Process each cascade
        for i in xrange(self.splitCount):

            source = self.shadowSources[i]

            # Find frustum section for this cascade
            splitParamStart = splitFunc(i) * relativeSplitSize
            splitParamEnd = splitFunc(i+1) * relativeSplitSize

            midPos = mixVector(nearPoint, farPoint, (splitParamStart + splitParamEnd) / 2.0 )
            topPlanePos = mixVector(trNearPoint, trFarPoint, splitParamEnd )

            filmSize = (topPlanePos - midPos).length() * 1.41
            midPos += camPos

            destPos = midPos + direction * 1.0

            # Set source position + rotation
            source.setPos(destPos)
            source.lookAt(midPos)
            source.setFilmSize(filmSize, filmSize)

            # Stable CSM Snapping
            # This snaps the source to its texel grids, so that there is no flickering
            # visible when the source moves. This works by projecting the 
            # Point (0,0,0) to light space, compute the texcoord differences and
            # offset the light world space position by that.
            mvp = Mat4(source.computeMVP())

            basePoint = mvp.xform(Point4(0,0,0,1))
            texelSize = 1.0 / float(source.resolution)
            
            basePoint *= 0.5 
            basePoint += Vec4(0.5)

            offsetX = basePoint.x % texelSize
            offsetY = basePoint.y % texelSize

            mvp.invertInPlace()
            newBase = mvp.xform(Point4( 
                (basePoint.x - offsetX) * 2.0 - 1.0, 
                (basePoint.y - offsetY) * 2.0 - 1.0, 
                (basePoint.z) * 2.0 - 1.0, 1))
            destPos -= Vec3(newBase.x, newBase.y, newBase.z)
            self.shadowSources[i].setPos(destPos)

            # Invalidate the source after changing the position
            self.shadowSources[i].invalidate()

        pstats_PSSM.stop()

    def __repr__(self):
        """ Generates a representative string for this object """
        return "DirectionalLight[pos=" + str(self.position) + ", dir=" + str(self.direction) + "]"
