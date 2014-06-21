

from panda3d.core import Vec3, Mat4, NodePath, LineSegs, Vec4


# Stores general data of a light and has to be seen
# as an interface.
class Light:


    # Stores data to be passed to the shader
    # Sadly passing arrays of structs isn't supported yet.
    # Othwerise it would be quite easier.
    class LightStruct:

        def __init__(self):

            # position in world space
            self.pos = Vec3(0)

            # light color
            self.col = Vec3(0)

            # radius of the light, for point lights for example
            self.radius = 1.0

            # light power. This could also be merged with the color
            # but for clearness it's excluded
            self.power = 1.0

            # projection matrix for this light
            self.projMatrix = Mat4()

            # for projectors (like for flashlights) specify which overlay to use
            # -1 means no overlay            
            self.posterIdx = -1

            # for shadow casting lights this is >= 0
            # specifies the position of the shadow map for this light in 
            # the shadow map texture array
            self.shadowIdx = -1


        def getDataMat(self):
            return Mat4(
                    self.pos.x,        self.pos.y,        self.pos.z,        self.radius,
                    self.col.x,        self.col.y,        self.col.z,        self.power,
                    self.shadowIdx,    self.posterIdx,    0.0,               0.0,
                    0.0,               0.0,               0.0,               0.0


                )            

        def getProjMat(self):
            return self.projMatrix

            

    def __init__(self):
        self.data = self.LightStruct()
        self.debugNode = NodePath("LightDebug")
        self.rotation = Vec3(0)
        self.visualizationNumSteps = 16
        self.dataNeedsUpdate = False
        self.shadowNeedsUpdate = False
        self.castShadows = False
        self.debugEnabled = False

    def setHpr(self, hpr):
        self.rotation = hpr
        self.queueUpdate()

    def setCastsShadows(self, shadows=True):
        self.castShadows = True

    def setPos(self, pos):
        self.data.pos = pos
        self.queueUpdate()

    def setColor(self, col):
        self.data.col = col
        self.queueUpdate()

    def needsUpdate(self):
        return self.dataNeedsUpdate

    def needsShadowUpdate(self):
        # no update needed if we have no shadows
        if not self.castShadows:
            return False
        return self.shadowNeedsUpdate

    def queueUpdate(self):
        self.dataNeedsUpdate = True

    def queueShadowUpdate(self):
        self.shadowNeedsUpdate = True

    def performUpdate(self):
        self.dataNeedsUpdate = False
        if self.castShadows:
            self._computeLightMat()

        if self.debugEnabled:
            self._updateDebugNode()


    def performShadowUpdate(self):
        slef.shadowNeedsUpdate = False

    def attachDebugNode(self, parent):
        self.debugNode.reparentTo(parent)
        self.debugEnabled = True
        self._updateDebugNode()

    def lookAt(self, pos):
        # todo
        pass

    def _computeLightMat(self):
        pass

    def _computeLightBounds(self):
        pass

    def _updateDebugNode(self):
        pass

    def _createDebugLine(self, points, connectToEnd = False):
        segs = LineSegs()
        segs.setThickness(1.0)
        segs.setColor(Vec4(1, 1, 0, 1))

        segs.moveTo(points[0])

        for point in points[1:]:
            segs.drawTo(point)

        if connectToEnd:
            segs.drawTo(points[0])

        return NodePath(segs.create())


