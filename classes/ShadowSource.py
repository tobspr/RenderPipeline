
from panda3d.core import Camera, PerspectiveLens, NodePath
from panda3d.core import CSYupRight, TransformState, CSZupRight
from panda3d.core import Mat4

from DebugObject import DebugObject

class ShadowSource(DebugObject):

    _GlobalShadowIndex = 1000

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
        self.atlasPos = 0,0
        self.doesHaveAtlasPos = False
        self.sourceIndex = 0

    def setSourceIndex(self, sourceIndex):
        self.sourceIndex = sourceIndex

    def getUid(self):
        return self.index

    def getMVP(self):
        projMat = Mat4.convertMat(
                CSYupRight, 
                self.lens.getCoordinateSystem()) * self.lens.getProjectionMat()
        transformMat = TransformState.makeMat(
                Mat4.convertMat(base.win.getGsg().getInternalCoordinateSystem(), 
                CSZupRight))
        modelViewMat = transformMat.invertCompose(render.getTransform(self.cameraNode)).getMat()
        return (modelViewMat * projMat)

    def assignAtlasPos(self, x, y):
        self.debug("Assigning atlas pos",x,"/",y)
        self.atlasPos = x, y
        self.doesHaveAtlasPos = True

    def getAtlasPos(self):
        return self.atlasPos

    def hasAtlasPos(self):
        return self.doesHaveAtlasPos

    def removeFromAtlas(self):
        self.doesHaveAtlasPos = False
        self.atlasPos = 0,0

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

    def setValid(self):
        self.valid = True

    def isValid(self):
        return self.valid



