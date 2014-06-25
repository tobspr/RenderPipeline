
import random
import math

from panda3d.core import GeomNode, NodePath, Geom, Vec3, Vec2, Vec4
from panda3d.core import GeomVertexFormat, GeomVertexData, GeomTriangles
from panda3d.core import GeomVertexWriter, GeomVertexReader, GeomTristrips


def posToIndex(pos):
    return str(int(pos.x * 100000)) + "|" +\
        str(int(pos.y * 100000)) + "|" +\
        str(int(pos.z * 100000))


class Vertex:

    def __init__(self, pos, nrm, texc, col):
        self.pos = self.roundPos(pos)
        self.nrm = nrm
        self.texc = texc
        self.keep = False
        self.col = Vec4(0,0,0, 1.0)
        self.triangles = []
        self.importance = 0.0

    def roundPos(self, pos):
        return Vec3(round(pos.x, 4), round(pos.y, 5), round(pos.z, 5))

    def setKeep(self, keep):
        self.keep = keep
        if keep:
            self.col = Vec4(0, 1, 0, 1)
        else:
            self.col = Vec4(1, 0, 0, 1)

    def distanceTo(self, other):
        p1 = self.pos
        p2 = other.pos

        distanceSquared = (p1.x-p2.x)**2 + (p1.y-p2.y)**2 + (p1.z-p2.z)**2
        return distanceSquared

        # return (self.pos - other.pos).length()

    def registerTriangle(self, tri):
        if tri not in self.triangles:
            self.triangles.append(tri)

    def __repr__(self):
        return "VTX[" + str(self.pos.x) + "," + str(self.pos.y) + "," + str(self.pos.z) + "; " + str(len(self.triangles)) + " Triangles]"


class Triangle:

    uid = 0

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c
        Triangle.uid += 1
        self.uid = Triangle.uid

    def getVertices(self):
        return [self.a, self.b, self.c]

    def __repr__(self):
        return "TRIANGLE[" + str(self.a) + ", " + str(self.b) + "," + str(self.c) + "]"

    def updateVertex(self, oldVtx, newVtx):
        if self.a is oldVtx:
            self.a = newVtx
        if self.b is oldVtx:
            self.b = newVtx
        if self.c is oldVtx:
            self.c = newVtx

    def isSame(self, other):
        vtxs = other.getVertices()

        if [self.a, self.b, self.c] == vtxs:
            return True

        if [self.b, self.c, self.a] == vtxs:
            return True

        if [self.c, self.a, self.b] == vtxs:
            return True


        return False

    def __eq__(self, other):
        return self.uid == other.uid

    def isEmpty(self):
        edgeLengthAB = self.a.distanceTo(self.b)
        edgeLengthBC = self.b.distanceTo(self.c)
        edgeLengthCA = self.c.distanceTo(self.a)

        if edgeLengthAB < 0.001 or edgeLengthBC < 0.001 or edgeLengthCA < 0.001:
            return True
        return False


class MeshSimplifier:

    def __init__(self):
        pass

    @classmethod
    def simplifyNodePath(self, np, wantedVertices = 500):

        print "Before:"
        np.analyze()

        resultNode = GeomNode("Simplified Mesh")

        geomNodes = np.findAllMatches('**/+GeomNode')
        for nodePath in geomNodes:
            geomNode = nodePath.node()
            for i in xrange(geomNode.getNumGeoms()):
                geom = geomNode.getGeom(i)
                state = geomNode.getGeomState(i)
                newGeom = self.simplifyGeom(geom, state, wantedVertices)
                if newGeom is not None:
                    resultNode.addGeom(newGeom, state)

        resultNP = NodePath(resultNode)

        print "After:"
        resultNP.flattenStrong()
        resultNP.analyze()

        return resultNP

    @classmethod
    def _extractVerticesAndTris(self, geom):
        vertices = {}
        rawVertices = []
        rawTriangles = []

        vertexData = geom.getVertexData()

        if vertexData.getFormat().getNumTexcoords() < 1:
            print "Geom has to have texcoords!"
            return False, False

        posReader = GeomVertexReader(vertexData, 'vertex')
        normReader = GeomVertexReader(vertexData, 'normal')
        texcReader = GeomVertexReader(vertexData, 'texcoord')

        # Extract vertices
        while not posReader.isAtEnd():
            pos = Vec3(posReader.getData3f())
            nrm = Vec3(normReader.getData3f())
            texc = Vec2(texcReader.getData2f())

            # should be normalized, but ..
            nrm.normalize()

            vtxID = posToIndex(pos)

            if vtxID in vertices:
                vtx = vertices[vtxID]
            else:
                vtx = Vertex(pos, nrm, texc, Vec3(0.1, 0.1, 0.1))
                vertices[vtxID] = vtx

            rawVertices.append(vtx)

        # Extract triangles
        rawTriangles = []

        for i in xrange(geom.getNumPrimitives()):
            primitive = geom.getPrimitive(i)

            if type(primitive) == GeomTristrips:
                print "Found GeomTristrips"

                for t in xrange(primitive.getNumPrimitives()):
                    start = primitive.getPrimitiveStart(t)
                    end = primitive.getPrimitiveEnd(t)

                    primitiveDefinitions = []
                    for vi in range(start, end):
                        index = primitive.getVertex(vi)
                        primitiveDefinitions.append(rawVertices[index])

                    numTrisStored = int(len(primitiveDefinitions) - 2)

                    invertOrder = True
                    for i in xrange(numTrisStored):
                        index = i
                        invertOrder = not invertOrder
                        data = primitiveDefinitions[index:index + 3]

                        # reverse each second triangle
                        # this is required for GeomTristrips
                        if not invertOrder:
                            wrapped = Triangle(*data)
                        else:
                            wrapped = Triangle(*reversed(data))
                        rawTriangles.append(wrapped)

            elif type(primitive) == GeomTriangles:
                print "Found GeomTriangles"

                for t in xrange(primitive.getNumPrimitives()):
                    start = primitive.getPrimitiveStart(t)
                    end = primitive.getPrimitiveEnd(t)

                    primitiveDefinitions = []
                    for vi in range(start, end):
                        index = primitive.getVertex(vi)
                        primitiveDefinitions.append(rawVertices[index])

                    firstData = primitiveDefinitions[0:3]
                    firstTri = Triangle(*firstData)
                    rawTriangles.append(firstTri)

        print len(rawTriangles), "triangles found"
        print len(rawVertices), "vertices found"
        print len(vertices.keys()), "unique vertices"

        for tri in rawTriangles:
            for vtx in [tri.a, tri.b, tri.c]:
                vtx.registerTriangle(tri)

        triangles = rawTriangles
        # todo: maybe needs more processing

        return vertices.values(), triangles

    @classmethod
    def _generateGeom(self, triangles):
        # Create geom instance
        geomFormat = GeomVertexFormat.getV3n3c4t2()
        geomData = GeomVertexData("vertices", geomFormat, Geom.UHStatic)

        # Create a new GeomTriangles
        trianglesGeom = GeomTriangles(Geom.UHStatic)

        # Get the writers
        posWriter = GeomVertexWriter(geomData, "vertex")
        normWriter = GeomVertexWriter(geomData, "normal")
        colorWriter = GeomVertexWriter(geomData, "color")
        texcWriter = GeomVertexWriter(geomData, "texcoord")

        geomData.setNumRows(len(triangles) * 3)

        currentIndex = 0

        vtxIndexes = {}

        for triangle in triangles:
            # print "Adding tri:",triangle
            indices = []

            for vertex in triangle.getVertices():
                
                if vertex in vtxIndexes:
                    indices.append(vtxIndexes[vertex])

                else:
                    posWriter.addData3f(vertex.pos)
                    texcWriter.addData2f(vertex.texc)
                    normWriter.addData3f(vertex.nrm)
                    colorWriter.addData4f(vertex.col)
                    vtxIndexes[vertex] = currentIndex
                    indices.append(currentIndex)
                    currentIndex += 1

            trianglesGeom.addVertices(*indices)

        newGeom = Geom(geomData)
        newGeom.addPrimitive(trianglesGeom)
        return newGeom

    @classmethod
    def _computeImportance(self, vertices, triangles, targetVerticeCount):

        if len(vertices) < 1:
            print "Mesh needs to have vertices!"
            return False

        handledVertices = []

        random.shuffle(vertices)

        print "Computing raw importance"
        distributed = []
        distribute = min(targetVerticeCount-1, len(vertices))

        # distributed.append(vertices[0])

        # # distribute = len(vertices) / 2

        # for i in xrange(distribute):
        #     print "Step",i

        #     nextVtx = None
        #     nextVtxDist = 0.0

        #     # find point farest away from all currently distributed
        #     for vtx in vertices:
        #         if vtx not in distributed:
        #             avgDist = 0.0
        #             avgSamples = 0

        #             # distance to all other distributed vertices
        #             for vtxD in distributed:
        #                 dist = vtxD.distanceTo(vtx)
        #                 avgDist += dist
        #                 avgSamples += 1

        #             avgDist /= float(avgSamples)

        #             if avgDist> nextVtxDist:
        #                 nextVtxDist = avgDist
        #                 nextVtx = vtx

        #     if nextVtx is not None:
        #         distributed.append(nextVtx)
        #     else:
        #         break



        random.shuffle(vertices)

        for i in xrange(distribute):
            distributed.append(vertices[i])




        print "Checked", len(distributed),"Vertices in!"

        for vtx in distributed:
            vtx.setKeep(True)


        print "Computing nearest vertices"
        for vtx in vertices:
            if not vtx.keep:
                # find nearest vertex to keep
                nextDist = 999999.0
                nextVtx = None
                for nvtx in vertices:
                    dist = nvtx.distanceTo(vtx)
                    if nvtx is not vtx and nvtx.keep and (dist < nextDist or nextVtx is None):
                        nextDist = dist
                        nextVtx = nvtx

                for tri in vtx.triangles:
                    tri.updateVertex(vtx, nextVtx)
                vtx.pos = nextVtx.pos

        return True

    @classmethod
    def simplifyGeom(self, geom, state, wantedVertices = 500):
        print "Simplifying geom .."

        # --- Extract triangles and verties ---
        print "Extracing vertices .."
        vertices, triangles = self._extractVerticesAndTris(geom)

        if vertices is False or triangles is False:
            print "Could not extract vertices!"
            return None

        # --- Compute vertex importance ---
        print "Computing importance .."
        if not self._computeImportance(vertices, triangles, wantedVertices):
            print "Could not compute importance"
            return None

        # --- Remove obsolete triangles ---
        print "Checking for obsolete triangles .."
        for triangle in triangles:
            if triangle.isEmpty():
                triangles.remove(triangle)

        # --- Remove equal triangles ---
        if True:
            print "Checking for equal triangles .."
            toRemove = []
            keep = []
            skipped = 0

            for index, triangle in enumerate(triangles):
                if triangle in toRemove:
                    skipped += 1
                    continue

                keep.append(triangle)

                for compared in triangles:
                    if ( triangle.isSame(compared)
                        and compared is not triangle
                        and compared not in keep
                        and compared not in toRemove):

                        toRemove.append(compared)



                # print index, "/ ", len(triangles), "remove:", len(toRemove), "skipped:", skipped

            print "Removing equal triangles .."
            for triangle in toRemove:
                if triangle in triangles:
                    triangles.remove(triangle)

        # --- Create new geom based on the computed triangles now ---
        newTriangles = triangles

        print "Generating new geom .."

        return self._generateGeom(newTriangles)
