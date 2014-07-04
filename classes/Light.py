

from panda3d.core import Vec3, NodePath, LineSegs, Vec4
from panda3d.core import OmniBoundingVolume
from panda3d.core import Mat4
from LightType import LightType

# Stores general data of a light and has to be seen
# as an interface.


class Light:

    # Stores data to be passed to the shader
    # Sadly passing arrays of structs isn't supported yet.
    # Othwerise it would be quite easier.
    # class LightStruct:

    #     def __init__(self):

    # position in world space
    #         self.pos = Vec3(0)

    # light color
    #         self.col = Vec3(0)

    # projection matrix for this light
    #         self.projMatrix = UnalignedLMatrix4()

    # for projectors (like for flashlights) specify which overlay to use
    # -1 means no overlay
    #         self.posterIdx = -1

    # for shadow casting lights this is >= 0
    # specifies the position of the shadow map for this light in
    # the shadow map texture array
    #         self.shadowIdx = -1

    # light type
    #         self.lightType = LightType.NoType

    # additional data
    #         self.additional = [0,0,0,0,0]

    # shadow atlas positions
    #         self.shadowIndices = [-2,-2,-2]

    #     def _updateDataMat(self):
    #         self._data_mat = UnalignedLMatrix4(
    #             self.lightType,          self.col.x,               self.col.y,              self.col.z,
    #             self.shadowIndices[0],   self.shadowIndices[1],    self.shadowIndices[2],   self.posterIdx,
    #             self.pos.x,              self.pos.y,               self.pos.z,              self.additional[4],
    #             self.additional[3],      self.additional[2],       self.additional[1],      self.additional[0]
    #         )

    #     def getDataMat(self):
    #         return self._data_mat

    #     def getProjMat(self):
    #         return self.projMatrix

    # Constructor
    def __init__(self):
        # self.data = self.LightStruct()
        self.debugNode = NodePath("LightDebug")
        self.visualizationNumSteps = 32
        self.dataNeedsUpdate = False
        self.castShadows = False
        self.debugEnabled = False
        self.bounds = OmniBoundingVolume()

        self.shadowSources = [None, None, None]

        self.lightType = self._getLightType()
        self.position = Vec3(0)
        self.color = Vec3(0)
        self.projectionMatrix = Mat4()
        self.posterIndex = -1
        self.rotation = Vec3(0)
        self.radius = 0.1

    @classmethod
    def getExposedAttributes(self):
        return {
            "position": "vec3",
            "color": "vec3",
            "projectionMatrix": "mat4",
            "posterIndex": "int",
            "lightType": "int",
            "radius": "float"
        }

    def setRadius(self, radius):
        self.radius = max(0.01, radius)
        self.queueUpdate()

    # Sets the rotation for this light
    def setHpr(self, hpr):
        self.rotation = hpr
        self.queueUpdate()

    # Returns true if the light casts shadows
    def hasShadows(self):
        return self.castShadows

    def setCastsShadows(self, shadows=True):
        self.castShadows = True

        if self.castShadows:
            self._initShadowSources()

    def setPos(self, pos):
        self.position = pos
        self.queueUpdate()
        self.queueShadowUpdate()

    def getBounds(self):
        return self.bounds

    def setColor(self, col):
        self.color = col
        self.queueUpdate()

    def needsUpdate(self):
        return self.dataNeedsUpdate

    def needsShadowUpdate(self):
        # no update needed if we have no shadows
        if not self.castShadows:
            return False

        for source in self.shadowSources:
            if source is not None and not source.isValid():
                return True

        return False

    def queueUpdate(self):
        self.dataNeedsUpdate = True

    def queueShadowUpdate(self):
        self.shadowNeedsUpdate = True

        for source in self.shadowSources:
            if source is not None:
                source.invalidate()

    def performUpdate(self):
        self.dataNeedsUpdate = False
        self._computeAdditionalData()
        self._computeLightBounds()

        if self.castShadows:
            self._computeLightMat()

        if self.debugEnabled:
            self._updateDebugNode()

    def performShadowUpdate(self):
        self._updateShadowSources()
        queued = []
        for source in self.shadowSources:
            if source is not None and not source.isValid():
                queued.append(source)
        self.shadowNeedsUpdate = not len(queued) < 1
        return queued

    # Attaches a node showing the bounds of this
    # light
    def attachDebugNode(self, parent):
        self.debugNode.reparentTo(parent)
        self.debugEnabled = True
        self._updateDebugNode()

    # Todo. Matches the light rotation so it looks at
    # that object
    def lookAt(self, pos):
        raise NotImplementedError()

    # Child classes should implement this
    def _computeLightMat(self):
        raise NotImplementedError()

    # Child classes should implement this
    def _computeLightBounds(self):
        raise NotImplementedError()

    # Child classes should implement this
    def _updateDebugNode(self):
        raise NotImplementedError()

    # Child classes should implement this
    def _computeAdditionalData(self):
        raise NotImplementedError()

    # Child classes should implement this
    def _getLightType(self):
        return LightType.NoType

    # Child classes should implement this
    def _initShadowSources(self):
        raise NotImplementedError()

    # Child classes should implement this
    def _updateShadowSources(self):
        raise NotImplementedError()

    # Adds a new shadow source
    def _setShadowSource(self, index, source):
        assert(index >= 0 and index < 3)
        # self.shadowSources[index] = source

        # self.shadowIndices[index] = -2

    def __repr__(self):
        return "AbstractLight[]"

    # Helper for visualizing the light bounds
    # Draws a line trough all points, if connectToEnd the last
    # point will get connected to the first point in the end
    def _createDebugLine(self, points, connectToEnd=False):
        segs = LineSegs()
        segs.setThickness(1.0)
        segs.setColor(Vec4(1, 1, 0, 1))

        segs.moveTo(points[0])

        for point in points[1:]:
            segs.drawTo(point)

        if connectToEnd:
            segs.drawTo(points[0])

        return NodePath(segs.create())
