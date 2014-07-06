
from Light import Light
from DebugObject import DebugObject

from panda3d.core import NodePath, Vec4, Vec3, BoundingSphere, Point3
from LightType import LightType
from ShadowSource import ShadowSource

import math


class PointLight(Light, DebugObject):

    def __init__(self):
        Light.__init__(self)
        DebugObject.__init__(self, "PointLight")
        self._spacing = 0.6
        self._bufferRadius = 1.0


    def _computeLightMat(self):

        hpr = [

            Vec3(0, 0, 0),
            Vec3(90, 0, 0),
            Vec3(180, 0, 0),
            Vec3(270, 0, 0),
            Vec3(0, 90, 0),
            Vec3(0, -90, 0),
        ]

        # for i in xrange(6):
        #     # self.shadowSources[i].setPos(self.position + Vec3(0,0.5,0))
        #     self.shadowSources[i].setPos(self.position)
        #     self.shadowSources[i].setHpr(hpr[i])

        self.shadowSources[0].setPos(self.position + Vec3(0,self._spacing*2.0,0))
        self.shadowSources[0].setHpr(Vec3(180,0,0))


        self.shadowSources[1].setPos(self.position - Vec3(0,self._spacing*2.0,0))
        self.shadowSources[1].setHpr(Vec3(0,0,0))
    
        # self.shadowSources[2].setPos(self.position - Vec3(0,0.5,0))
        # self.shadowSources[2].setHpr(Vec3(90,0,0))

        # self.shadowSources[3].setPos(self.position - Vec3(0,0.5,0))
        # self.shadowSources[3].setHpr(Vec3(270,0,0))


        # self.debug("Compute Light mat")
        pass

    def _getLightType(self):
        return LightType.Point

    def _computeLightBounds(self):
        self.bounds = BoundingSphere(Point3(self.position), self.radius)
        # self.bounds.showBounds(render)

    def _computeAdditionalData(self):
        pass

    def _updateDebugNode(self):
        # self.debug("updating debug node")

        mainNode = NodePath("DebugNodeInner")
        mainNode.setPos(self.position)

        # inner = loader.loadModel("Assets/Visualisation/Lamp")
        # inner.setPos(-0.5, -0.5, 0.0)
        # inner.setScale(0.5)
        # inner.setColorScale(Vec4(1,1,0,1))
        # inner.reparentTo(mainNode)

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
        # mainNode.setHpr(self.rotation)

        mainNode.flattenStrong()

        self.debugNode.node().removeAllChildren()
        mainNode.reparentTo(self.debugNode)


    def _initShadowSources(self):
        
        for i in xrange(2):
            source = ShadowSource()
            source.setupPerspectiveLens( self._spacing, self.radius + self._spacing + self._bufferRadius, (90,90) )
            source.setResolution(2048)
            self._addShadowSource(source)

    def _updateShadowSources(self):
        pass

    def __repr__(self):
        return "PointLight[pos="+str(self.position)+", radius="+str(self.radius)+"]"