

from panda3d.core import Vec3, NodePath, LineSegs, Vec4
from panda3d.core import OmniBoundingVolume
from panda3d.core import Mat4, PTAInt
from LightType import LightType
from DebugObject import DebugObject

# Stores general data of a light and has to be seen
# as an interface.
class Light:

    # Constructor
    def __init__(self):
        DebugObject.__init__(self, "AbstractLight")
        self.debugNode = NodePath("LightDebug")
        self.visualizationNumSteps = 32
        self.dataNeedsUpdate = False
        self.castShadows = False
        self.debugEnabled = False
        self.bounds = OmniBoundingVolume()

        self.shadowSources = []
        self.lightType = self._getLightType()
        self.position = Vec3(0)
        self.color = Vec3(0)
        self.posterIndex = -1
        self.rotation = Vec3(0)
        self.radius = 0.1

        self.sourceIndexes = PTAInt.emptyArray(6)
        for i in xrange(6):
            self.sourceIndexes[i] = -1

        

    @classmethod
    def getExposedAttributes(self):
        return {
            "position": "vec3",
            "color": "vec3",
            "posterIndex": "int",
            "lightType": "int",
            "radius": "float",
            "sourceIndexes": "array<int>(6)",
        }

    # Todo. Matches the light rotation so it looks at
    # that object
    def lookAt(self, pos):
        raise NotImplementedError()


    def setRadius(self, radius):
        self.radius = max(0.01, radius)
        self.queueUpdate()

    def getShadowSources(self):
        return self.shadowSources

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
            if not source.isValid():
                return True

        return False

    def queueUpdate(self):
        self.dataNeedsUpdate = True

    def queueShadowUpdate(self):
        self.shadowNeedsUpdate = True

        for source in self.shadowSources:
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
            if not source.isValid():
                queued.append(source)
        self.shadowNeedsUpdate = not len(queued) < 1
        return queued

    # Attaches a node showing the bounds of this
    # light
    def attachDebugNode(self, parent):
        self.debugNode.reparentTo(parent)
        self.debugEnabled = True
        self._updateDebugNode()

    def setSourceIndex(self, sourceId, index):
        self.debug("light.sourceIndexes["+str(sourceId)+"] = "+ str(index))
        self.sourceIndexes[sourceId] = index

    # Adds a new shadow source
    def _addShadowSource(self, source):
        if source in self.shadowSources:
            self.warning("Shadow source already exists!")
            return 

        self.shadowSources.append(source)
        self.queueShadowUpdate()

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
