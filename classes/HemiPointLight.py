
from Light import Light
from DebugObject import DebugObject

from panda3d.core import NodePath, LineSegs, Vec4, Vec3, BoundingSphere, Point3
from LightType import LightType

import math


class HemiPointLight (Light, DebugObject):

    def __init__(self):
        Light.__init__(self)
        DebugObject.__init__(self, "HemiPointLight")
        self.radius = 0.0

    def _computeLightMat(self):
        pass

    def _getLightType(self):
        return LightType.HemiPoint

    def _computeLightBounds(self):
        self.bounds = BoundingSphere(Point3(self.data.pos), self.radius)

    def _computeAdditionalData(self):
        self.data.additional[0] = self.radius


    def _updateDebugNode(self):
        # self.debug("updating debug node")

        mainNode = NodePath("DebugNodeInner")
        mainNode.setPos(self.data.pos)

        inner = loader.loadModel("Assets/Visualisation/Lamp")
        inner.setPos(-0.5, -0.5, 0.0)
        inner.setScale(0.5)
        inner.setColorScale(Vec4(1,1,0,1))
        inner.reparentTo(mainNode)

        lineNode = mainNode.attachNewNode("lines")

        # Outer circle
        points = []
        for i in xrange(self.visualizationNumSteps + 1):
            angle = float(i) / float(self.visualizationNumSteps) * math.pi * 2.0
            points.append(Vec3(0, math.sin(angle), math.cos(angle)))
        self._createDebugLine(points, False).reparentTo(lineNode)

        # Horizontal circle
        points = []
        for i in xrange(self.visualizationNumSteps / 2 + 1):
            angle = float(i) / float(self.visualizationNumSteps) * math.pi * 2.0
            points.append(Vec3(math.sin(angle), math.cos(angle), 0))
        self._createDebugLine(points, False).reparentTo(lineNode)

        # Vertical circle
        points = []
        for i in xrange(self.visualizationNumSteps / 2 + 1):
            angle = float(i) / float(self.visualizationNumSteps) * math.pi * 2.0
            points.append(Vec3(math.sin(angle), 0, math.cos(angle)))
        self._createDebugLine(points, False).reparentTo(lineNode)

        lineNode.setScale(self.radius)
        mainNode.setHpr(self.rotation)

        self.debugNode.node().removeAllChildren()
        mainNode.reparentTo(self.debugNode)

    def setRadius(self, radius):
        self.radius = max(0.01, radius)
        self.queueUpdate()


