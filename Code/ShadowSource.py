
from panda3d.core import Camera, PerspectiveLens, NodePath, OrthographicLens
from panda3d.core import CSYupRight, TransformState, CSZupRight
from panda3d.core import UnalignedLMatrix4f
from panda3d.core import Vec2, Mat4

from DebugObject import DebugObject
from ShaderStructArray import ShaderStructElement
from Globals import Globals


class ShadowSource(DebugObject, ShaderStructElement):

    """ This class can be seen as a camera. It stores the necessary data to 
    generate and store the shadow map for the assigned lens (like computing the MVP), 
    and also stores information about the shadowmap, like position in the 
    shadow atlas, or resolution. Each ShadowSource has a unique index, 
    which is used by the lights to identify which sources belong to it.
    """

    # Store a global index for assigning unique ids to the instances
    _GlobalShadowIndex = 999

    @classmethod
    def getExposedAttributes(self):
        return {
            "resolution": "int",
            "atlasPos": "vec2",
            "mvp": "mat4",
            "nearPlane": "float",
            "farPlane": "float"
        }

    @classmethod
    def _generateUID(self):
        """ Generates an uid and returns that """
        self._GlobalShadowIndex += 1
        return self._GlobalShadowIndex

    def __init__(self):
        """ Creates a new ShadowSource. After the creation, a lens can be added
        with setupPerspectiveLens or setupOrtographicLens. """
        self.index = self._generateUID()
        DebugObject.__init__(self, "ShadowSource-" + str(self.index))
        ShaderStructElement.__init__(self)

        self.valid = False
        self.camera = Camera("ShadowSource-" + str(self.index))
        self.camera.setActive(False)
        self.cameraNode = NodePath(self.camera)
        self.cameraNode.reparentTo(Globals.render)
        self.cameraNode.hide()
        self.resolution = 512
        self.atlasPos = Vec2(0)
        self.doesHaveAtlasPos = False
        self.sourceIndex = 0
        self.mvp = UnalignedLMatrix4f()
        self.sourceIndex = -1
        self.nearPlane = 0.0
        self.farPlane = 1000.0
        self.converterYUR = None
        self.transforMat = TransformState.makeMat(
            Mat4.convertMat(Globals.base.win.getGsg().getInternalCoordinateSystem(),
                            CSZupRight))
            
    def cleanup(self):
        """ Cleans up the shadow source """
        self.cameraNode.removeNode()

    def setFilmSize(self, size_x, size_y):
        """ Sets the film size of the source, this is equivalent to setFilmSize
        on a Lens. """
        self.lens.setFilmSize(size_x, size_y)
        self.rebuildMatrixCache()

    def getLens(self):
        """ Returns the source lens """
        return self.lens

    def getSourceIndex(self):
        """ Returns the assigned source index. The source index is the index
        of the ShadowSource in the ShadowSources array of the assigned
        Light. """
        return self.sourceIndex

    def getUID(self):
        """ Returns the uid of the shadow source """
        return self.index

    def setSourceIndex(self, index):
        """ Sets the source index of this source. This is called by the light,
        as only the light knows at which position this source is in the
        Sources array. """
        self.sourceIndex = index

    def computeMVP(self):
        """ Computes the modelViewProjection matrix for the lens. Actually,
        this is the worldViewProjection matrix, but for convenience it is
        called mvp. """

        self.rebuildMatrixCache()
        projMat = self.converterYUR
        # modelViewMat = self.transforMat.invertCompose(
        modelViewMat = Globals.render.getTransform(self.cameraNode).getMat()
        return UnalignedLMatrix4f(modelViewMat * projMat)

    def assignAtlasPos(self, x, y):
        """ Assigns this source a position in the shadow atlas. This is called
        by the shadow atlas. Coordinates are float from 0 .. 1 """
        self.atlasPos = Vec2(x, y)
        self.doesHaveAtlasPos = True

    def update(self):
        """ Updates the shadow source. Currently only recomputes the mvp and
        triggers an array update """
        self.mvp = self.computeMVP()
        self.onPropertyChanged()

    def getAtlasPos(self):
        """ Returns the assigned atlas pos, if present. Coordinates are float
        from 0 .. 1 """
        return self.atlasPos

    def hasAtlasPos(self):
        """ Returns wheter this ShadowSource has already a position in the
        shadow atlas, or is currently unassigned """
        return self.doesHaveAtlasPos

    def removeFromAtlas(self):
        """ Deletes the atlas coordinates, this gets called by the atlas after the
        Source got removed from the atlas """
        self.doesHaveAtlasPos = False
        self.atlasPos = Vec2(0)

    def setResolution(self, resolution):
        """ Sets the resolution in pixels of this shadow source. Has to be
        a multiple of the tileSize specified in LightManager """
        assert(resolution > 1 and resolution <= 8192)
        self.resolution = resolution

    def getResolution(self):
        """ Returns the resolution of the shadow source in pixels """
        return self.resolution

    def setupPerspectiveLens(self, near=0.1, far=100.0, fov=(90, 90)):
        """ Setups a PerspectiveLens with a given near plane, far plane
        and FoV. The FoV is a tuple in the format (Horizontal FoV, Vertical FoV) """
        self.lens = PerspectiveLens()
        self.lens.setNearFar(near, far)
        self.lens.setFov(fov[0], fov[1])
        self.camera.setLens(self.lens)
        self.nearPlane = near
        self.farPlane = far
        self.rebuildMatrixCache()

    def setLens(self, lens):
        """ Setups the ShadowSource to use an external lens """
        self.lens = lens
        self.camera.setLens(self.lens)
        self.nearPlane = lens.getNear()
        self.farPlane = lens.getFar()
        self.nearPlane = 0.5
        self.farPlane = 50.0
        self.rebuildMatrixCache()

    def setupOrtographicLens(self, near=0.1, far=100.0, filmSize=(512, 512)):
        """ Setups a OrtographicLens with a given near plane, far plane
        and film size. The film size is a tuple in the format (filmWidth, filmHeight)
        in world space. """
        self.lens = OrthographicLens()
        self.lens.setNearFar(near, far)
        self.lens.setFilmSize(*filmSize)
        self.camera.setLens(self.lens)
        self.nearPlane = near
        self.farPlane = far
        self.rebuildMatrixCache()

    def rebuildMatrixCache(self):
        """ Internal method to precompute a part of the MVP to improve performance"""
        self.converterYUR = self.lens.getProjectionMat()

    def setPos(self, pos):
        """ Sets the position of the source in world space """
        self.cameraNode.setPos(pos)

    def getPos(self):
        """ Returns the position of the source in world space """
        return self.cameraNode.getPos()

    def setHpr(self, hpr):
        """ Sets the rotation of the source in world space """
        self.cameraNode.setHpr(hpr)

    def lookAt(self, pos):
        """ Looks at a point (in world space) """
        self.cameraNode.lookAt(pos.x, pos.y, pos.z)

    def invalidate(self):
        """ Invalidates this shadow source, means telling the LightManager
        that the shadow map for this light should be rebuilt. Otherwise it
        won't get refreshed. """
        self.valid = False

    def setValid(self):
        """ The LightManager calls this after the shadow map got updated
        successfully """
        self.valid = True

    def isValid(self):
        """ Returns wether the shadow map is still valid or should be refreshed """
        return self.valid

    def __repr__(self):
        """ Returns a representative string of this instance """
        return "ShadowSource[id=" + str(self.index) + "]"

    def __hash__(self):
        return self.index

    def onUpdated(self):
        """ Gets called when shadow source was updated """
