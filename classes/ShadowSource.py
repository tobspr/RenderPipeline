
from panda3d.core import Camera, PerspectiveLens, NodePath, Mat4
from panda3d.core import CSYupRight, TransformState, CSZupRight

class ShadowSource:

    _GlobalShadowIndex = 0

    def __init__(self):
        self.valid = True
        self.index = self._GlobalShadowIndex
        self._GlobalShadowIndex += 1
        self.camera = Camera("ShadowSource-" + str(self.index))
        self.cameraNode = NodePath(self.camera)
        self.cameraNode.reparentTo(render)
        self.camera.showFrustum()
        self.resolution = 512
        self.lod = 0


    def getMVP(self):
        projMat = Mat4.convertMat(
                CSYupRight, 
                self.lens.getCoordinateSystem()) * self.lens.getProjectionMat()
        transformMat = TransformState.makeMat(
                Mat4.convertMat(base.win.getGsg().getInternalCoordinateSystem(), 
                CSZupRight))
        modelViewMat = transformMat.invertCompose(render.getTransform(self.cameraNode)).getMat()
        return modelViewMat * projMat


    def setResolution(self, resolution):
        self.resolution = resolution

    def getResolution(self):
        return self.resolution

    def setupPerspectiveLens(self, near=0.1, far=100.0, fov=(90,90)):
        self.lens = PerspectiveLens()
        self.lens.setNearFar(near, far)
        self.lens.setFov(fov[0], fov[1])
        self.camera.setLens(self.lens)

    def setPos(self, pos):
        self.cameraNode.setPos(pos)

    def setHpr(self, hpr):
        self.cameraNode.setHpr(hpr)

    def lookAt(self, pos):
        self.cameraNode.lookAt(pos.x, pos.y, pos.z)

    def invalidate(self):
        self.valid = False

    def isValid(self):
        return self.valid



