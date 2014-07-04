
from panda3d.core import Camera, PerspectiveLens, NodePath
from panda3d.core import CSYupRight, TransformState, CSZupRight, UnalignedLMatrix4f
from panda3d.core import Mat4, Vec2

from DebugObject import DebugObject


class ShadowSource(DebugObject):

    _GlobalShadowIndex = 1000

    @classmethod
    def getExposedAttributes(self):
        return {
            "resolution": "float",
            "lod": "float",
            "atlasPos": "vec2",
            "mvp": "mat4",
            "nearPlane": "float",
            "farPlane": "float"
        }

    def __init__(self):
        DebugObject.__init__(self, "ShadowSource")
        self.valid = False
        ShadowSource._GlobalShadowIndex += 1
        self.index = ShadowSource._GlobalShadowIndex
        self.camera = Camera("ShadowSource-" + str(self.index))
        self.cameraNode = NodePath(self.camera)
        self.cameraNode.reparentTo(render)
        # self.camera.showFrustum()
        self.resolution = 1024
        self.lod = 0
        self.atlasPos = Vec2(0)
        self.doesHaveAtlasPos = False
        self.sourceIndex = 0
        self.mvp = Mat4()
        self.sourceIndex = -1
        self.nearPlane = 0.0
        self.farPlane = 1000.0

    def getSourceIndex(self):
        return self.sourceIndex

    def getUid(self):
        return self.index

    def __repr__(self):
        return "ShadowSource[id=" + str(self.index) + "]"

    def setSourceIndex(self, index):
        self.debug("Assigning index", index)
        self.sourceIndex = index

    def computeMVP(self):
        projMat = Mat4.convertMat(
            CSYupRight,
            self.lens.getCoordinateSystem()) * self.lens.getProjectionMat()
        transformMat = TransformState.makeMat(
            Mat4.convertMat(base.win.getGsg().getInternalCoordinateSystem(),
                            CSZupRight))
        modelViewMat = transformMat.invertCompose(
            render.getTransform(self.cameraNode)).getMat()
        self.mvp = UnalignedLMatrix4f(modelViewMat * projMat)

    def assignAtlasPos(self, x, y):
        self.debug("Assigning atlas pos", x, "/", y)
        self.atlasPos = Vec2(x, y)
        self.doesHaveAtlasPos = True

    def update(self):
        self.computeMVP()

    def getAtlasPos(self):
        return self.atlasPos

    def hasAtlasPos(self):
        return self.doesHaveAtlasPos

    def removeFromAtlas(self):
        self.doesHaveAtlasPos = False
        self.atlasPos = Vec2(0)

    def setResolution(self, resolution):
        self.resolution = resolution

    def getResolution(self):
        return self.resolution

    def setupPerspectiveLens(self, near=0.1, far=100.0, fov=(90, 90)):
        self.lens = PerspectiveLens()
        self.lens.setNearFar(near, far)
        self.lens.setFov(fov[0], fov[1])
        self.camera.setLens(self.lens)
        self.nearPlane = near
        self.farPlane = far

    def setPos(self, pos):
        self.cameraNode.setPos(pos)

    def setHpr(self, hpr):
        self.cameraNode.setHpr(hpr)

    def lookAt(self, pos):
        self.cameraNode.lookAt(pos.x, pos.y, pos.z)

    def invalidate(self):
        self.valid = False

    def setValid(self):
        self.valid = True

    def isValid(self):
        return self.valid
