
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
        """ Creates a new spot light. Remember to set a position
        and an orientation """
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
        # mainNode = NodePath("DebugNodeInner")
        # mainNode.setPos(self.position)
        # lineNode = mainNode.attachNewNode("lines")

        # inner = Globals.loader.loadModel("box")
        # inner.setPos(-0.5, -0.5, 0.6)
        # inner.flattenStrong()
        # inner.reparentTo(mainNode)

        # # Generate outer circles
        # points1 = []
        # points2 = []
        # points3 = []
        # for i in range(self.visualizationNumSteps + 1):
        #     angle = float(
        #         i) / float(self.visualizationNumSteps) * math.pi * 2.0
        #     points1.append(Vec3(0, math.sin(angle), math.cos(angle)))
        #     points2.append(Vec3(math.sin(angle), math.cos(angle), 0))
        #     points3.append(Vec3(math.sin(angle), 0, math.cos(angle)))

        # self._createDebugLine(points1, False).reparentTo(lineNode)
        # self._createDebugLine(points2, False).reparentTo(lineNode)
        # self._createDebugLine(points3, False).reparentTo(lineNode)

        # lineNode.setScale(self.radius)
        # mainNode.flattenStrong()
        # self.debugNode.node().removeAllChildren()
        # mainNode.reparentTo(self.debugNode)

    def _initShadowSources(self):
        """ Internal method to init the shadow sources """
        # for i in range(2):
        #     source = ShadowSource()
        #     source.setupPerspectiveLens(
        #         self.spacing, self.radius + self.spacing + self.bufferRadius, (160, 160))
        #     source.setResolution(self.shadowResolution)
        #     self._addShadowSource(source)

        source = ShadowSource()
        source.setupPerspectiveLens(
            self.nearPlane, self.radius, (self.spotSize.x, self.spotSize.y))
        source.setResolution(self.shadowResolution)
        self._addShadowSource(source)

    def _updateShadowSources(self):
        """ Recomputes the position of the shadow sources. One
        Source is facing to +x, and the other one to -x. This
        gives a 360 degree view. """

        self.shadowSources[0].setPos(self.position)
        self.shadowSources[0].lookAt(self.position + self.direction)

        # self.shadowSources[0].setPos(
        #     self.position + Vec3(0, self.spacing * 2.0, 0))
        # self.shadowSources[0].setHpr(Vec3(180, 0, 0))

        # self.shadowSources[1].setPos(
        #     self.position - Vec3(0, self.spacing * 2.0, 0))
        # self.shadowSources[1].setHpr(Vec3(0, 0, 0))

    def __repr__(self):
        """ Generates a string representation of this instance """
        return "SpotLight[id=" + str(self.structElementID) + "]"
