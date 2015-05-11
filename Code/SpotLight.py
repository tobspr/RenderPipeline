
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

    def getLightType(self):
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
        innerNode.setColorScale(1,1,0,1)

        # Create the outer lines
        lineNode = debugNode.attachNewNode("lines")

        currentNodeTransform = render.getTransform(self.ghostCameraNode).getMat()
        currentCamTransform = self.ghostLens.getProjectionMat()
        currentRelativeCamPos = self.ghostCameraNode.getPos(render)
        currentCamBounds = self.ghostLens.makeBounds()
        currentCamBounds.xform(self.ghostCameraNode.getMat(render))

        p = lambda index: currentCamBounds.getPoint(index)

        # Make a circle at the bottom
        frustumBottomCenter = (p(0) + p(1) + p(2) + p(3)) * 0.25
        upVector = (p(0) + p(1)) / 2 - frustumBottomCenter
        rightVector = (p(1) + p(2)) / 2 - frustumBottomCenter
        points = []
        for idx in xrange(64):
            rad = idx / 64.0 * math.pi * 2.0
            pos = upVector * math.sin(rad) + rightVector * math.cos(rad)
            pos += frustumBottomCenter
            points.append(pos)
        frustumLine = self._createDebugLine(points, True)
        frustumLine.setColorScale(1,1,0,1)
        frustumLine.reparentTo(lineNode)


        # Create frustum lines which connect the origin to the bottom circle
        pointArrays = [
            [self.position, frustumBottomCenter + upVector],
            [self.position, frustumBottomCenter - upVector],
            [self.position, frustumBottomCenter + rightVector],
            [self.position, frustumBottomCenter - rightVector],
        ]

        for pointArray in pointArrays:
            frustumLine = self._createDebugLine(pointArray, False)
            frustumLine.setColorScale(1,1,0,1)
            frustumLine.reparentTo(lineNode)

        # Create line which is in the direction of the spot light
        startPoint = (p(0) + p(1) + p(2) + p(3)) * 0.25
        endPoint = (p(4) + p(5) + p(6) + p(7)) * 0.25
        line = self._createDebugLine([startPoint, endPoint], False)
        line.setColorScale(1,1,1,1)
        line.reparentTo(lineNode)

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

    def __repr__(self):
        """ Generates a string representation of this instance """
        return "SpotLight[]"
