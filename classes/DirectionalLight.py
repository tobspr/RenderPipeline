
from Light import Light
from DebugObject import DebugObject

from panda3d.core import NodePath, Vec4, Vec3, OmniBoundingVolume, Point3
from LightType import LightType
from ShadowSource import ShadowSource

import math


class DirectionalLight(Light, DebugObject):

    def __init__(self):
        Light.__init__(self)
        DebugObject.__init__(self, "DirectionalLight")

        self._spacing = 0.6
        self.radius = 99999999999.0
        self.position = Vec3(0)
        self.bounds = OmniBoundingVolume()


    def _computeLightMat(self):
        pass


    def _getLightType(self):
        return LightType.Directional

    def _computeLightBounds(self):
        pass

    # directional light has no radius
    def setRadius(self, x):
        pass

    # directional light has no position
    def setPos(self, x):
        pass

    def _computeAdditionalData(self):
        pass

    def _updateDebugNode(self):
        # self.debug("updating debug node")
        pass
        # mainNode = NodePath("DebugNodeInner")
        # mainNode.setPos(self.position)

        # inner = loader.loadModel("Assets/Visualisation/Lamp")
        # inner.setPos(-0.5, -0.5, 0.0)
        # inner.setScale(0.5)
        # inner.setColorScale(Vec4(1,1,0,1))
        # inner.reparentTo(mainNode)

        # lineNode = mainNode.attachNewNode("lines")

        # # Outer circles
        # points1 = []
        # points2 = []
        # points3 = []
        # for i in xrange(self.visualizationNumSteps + 1):
        #     angle = float(i) / float(self.visualizationNumSteps) * math.pi * 2.0
        #     points1.append(Vec3(0, math.sin(angle), math.cos(angle)))
        #     points2.append(Vec3(math.sin(angle), math.cos(angle), 0))
        #     points3.append(Vec3(math.sin(angle), 0, math.cos(angle)))

        # self._createDebugLine(points1, False).reparentTo(lineNode)
        # self._createDebugLine(points2, False).reparentTo(lineNode)
        # self._createDebugLine(points3, False).reparentTo(lineNode)

        # lineNode.setScale(self.radius)
        # mainNode.setHpr(self.rotation)

        # mainNode.flattenStrong()

        # self.debugNode.node().removeAllChildren()
        # mainNode.reparentTo(self.debugNode)


    def _initShadowSources(self):
        pass
        # for i in xrange(2):
        #     source = ShadowSource()
        #     source.setupPerspectiveLens( self._spacing, self.radius + self._spacing, (90,90) )
        #     source.setResolution(1024)
        #     self._addShadowSource(source)

    def _updateShadowSources(self):
        pass

    def __repr__(self):
        return "DirectionalLight[pos="+str(self.position)+", radius="+str(self.radius)+",dir="+str(self.direction) + "]"