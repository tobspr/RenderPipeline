
import math

from panda3d.core import NodePath, Vec4, Vec3, BoundingSphere, Point3, Point2
from panda3d.core import OmniBoundingVolume, Vec2, PerspectiveLens, Camera
from panda3d.core import TransformState, CSZupRight, Mat4, CSYupRight, CardMaker

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

        # Used to compute the MVP
        self.ghostCamera = Camera("PointLight")
        self.ghostLens = PerspectiveLens()
        self.ghostLens.setFov(130)
        self.ghostCamera.setLens(self.ghostLens)
        self.ghostCameraNode = NodePath(self.ghostCamera)
        self.ghostCameraNode.reparentTo(Globals.render)

    def _getLightType(self):
        """ Internal method to fetch the type of this light, used by Light """
        return LightType.Spot

    def _updateLens(self):
        """ Internal method which gets called when the lens properties changed """
        for source in self.shadowSources:
            source.rebuildMatrixCache()

    def cleanup(self):
        """ Internal method which gets called when the light got deleted """
        self.ghostCameraNode.removeNode()
        Light.cleanup(self)

    def setFov(self, fov):
        """ Sets the field of view of the spotlight """
        self.ghostLens.setFov(fov)
        self._updateLens()

    def setPos(self, pos):
        """ Sets the position of the spotlight """
        self.ghostCameraNode.setPos(pos)
        Light.setPos(self, pos)

    def lookAt(self, pos):
        """ Makes the spotlight look at the given position """
        self.ghostCameraNode.lookAt(pos)

    def _computeAdditionalData(self):
        """ Internal method to recompute the spotlight MVP """
        self.ghostCameraNode.setPos(self.position)

        transMat = TransformState.makeMat(
            Mat4.convertMat(Globals.base.win.getGsg().getInternalCoordinateSystem(),
                            CSZupRight))

        converterMat = Mat4.convertMat(CSYupRight, 
            self.ghostLens.getCoordinateSystem()) * self.ghostLens.getProjectionMat()
        modelViewMat = transMat.invertCompose(
            Globals.render.getTransform(self.ghostCameraNode)).getMat()

        self.mvp = modelViewMat * converterMat

        # print "computed mvp here"

    def _computeLightBounds(self):
        """ Recomputes the bounds of this light. For a SpotLight, we for now
        use a simple BoundingSphere """
        self.bounds = BoundingSphere(Point3(self.position), self.radius * 2.0)

    def setNearFar(self, near, far):
        """ Sets the near and far plane of the spotlight """
        self.nearPlane = near
        self.radius = far
        self.ghostLens.setNearFar(near, far)
        self._updateLens()

    def _updateDebugNode(self):
        """ Internal method to generate new debug geometry. """
        debugNode = NodePath("SpotLightDebugNode")

        # Create the inner image 
        cm = CardMaker("SpotLightDebug")
        cm.setFrameFullscreenQuad()
        innerNode = NodePath(cm.generate())
        innerNode.setTexture(Globals.loader.loadTexture("Data/GUI/Visualization/SpotLight.png"))
        innerNode.setBillboardPointEye()
        innerNode.reparentTo(debugNode)
        innerNode.setPos(self.position)

        # Create the outer lines
        lineNode = debugNode.attachNewNode("lines")

        currentNodeTransform = render.getTransform(self.ghostCameraNode).getMat()
        currentCamTransform = self.ghostLens.getProjectionMat()
        currentRelativeCamPos = self.ghostCameraNode.getPos(render)
        currentCamBounds = self.ghostLens.makeBounds()
        currentCamBounds.xform(self.ghostCameraNode.getMat(render))

        pointArrays = [
            [1, 0, 4, 5, 1, 2, 6, 5],
            [0, 3, 7, 4],
            [7, 6, 2, 3],
        ]

        for pointArray in pointArrays:
            for i, val in enumerate(pointArray):
                pointArray[i] = currentCamBounds.getPoint(val)

            self._createDebugLine(pointArray, False).reparentTo(lineNode)

        # Remove the old debug node
        self.debugNode.node().removeAllChildren()

        # Attach the new debug node
        debugNode.reparentTo(self.debugNode)
        # self.debugNode.flattenStrong()

    def _initShadowSources(self):
        """ Internal method to init the shadow sources """
        source = ShadowSource()
        source.setResolution(self.shadowResolution)
        source.setLens(self.ghostLens)
        self._addShadowSource(source)

    def _updateShadowSources(self):
        """ Recomputes the position of the shadow source """
        self.shadowSources[0].setPos(self.position)
        self.shadowSources[0].setHpr(self.ghostCameraNode.getHpr())



        # self._computeAdditionalData()

        # self.shadowSources[0].setLens(self.ghostLens)

        # print self.shadowSources[0].getLens() == self.ghostLens
        # print self.shadowSources[0].getLens().getProjectionMat()
        # print self.ghostLens.getProjectionMat()

        # print "\n\n"
        # print Mat4(self.shadowSources[0].computeMVP())
        # print "VS"
        # print self.mvp

    def __repr__(self):
        """ Generates a string representation of this instance """
        return "SpotLight[]"
