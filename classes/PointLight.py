
from Light import Light
from DebugObject import DebugObject

from panda3d.core import NodePath, LineSegs, Vec4, Vec3, BoundingSphere, Point3
from LightType import LightType
from ShadowSource import ShadowSource

import math


class PointLight(Light, DebugObject):

    def __init__(self):
        Light.__init__(self)
        DebugObject.__init__(self, "HemiPointLight")
        self.radius = 0.0

    def _computeLightMat(self):
        pass

    def _getLightType(self):
        return LightType.Point

    def _computeLightBounds(self):
        self.bounds = BoundingSphere(Point3(self.data.pos), self.radius)
        # self.bounds.showBounds(render)

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

        # Outer circles
        points1 = []
        points2 = []
        points3 = []
        for i in xrange(self.visualizationNumSteps + 1):
            angle = float(i) / float(self.visualizationNumSteps) * math.pi * 2.0
            points1.append(Vec3(0, math.sin(angle), math.cos(angle)))
            points2.append(Vec3(math.sin(angle), math.cos(angle), 0))
            points3.append(Vec3(math.sin(angle), 0, math.cos(angle)))

        self._createDebugLine(points1, False).reparentTo(lineNode)
        self._createDebugLine(points2, False).reparentTo(lineNode)
        self._createDebugLine(points3, False).reparentTo(lineNode)


        lineNode.setScale(self.radius)
        mainNode.setHpr(self.rotation)

        mainNode.flattenStrong()

        self.debugNode.node().removeAllChildren()
        mainNode.reparentTo(self.debugNode)

    def setRadius(self, radius):
        self.radius = max(0.01, radius)
        self.queueUpdate()

    def _initShadowSources(self):
        
        demoSource = ShadowSource()

        self._addShadowSource(demoSource)


    def _updateShadowSources(self):
        pass




    def __repr__(self):
        return "PointLight[pos="+str(self.data.pos)+", radius="+str(self.radius)+"]"