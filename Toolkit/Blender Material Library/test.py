

from panda3d.core import *
import direct.directbase.DirectStart


l = loader.loadModel("DefaultScene.bam")
l.ls()


geomNodeCollection = l.findAllMatches('**/+GeomNode')
for nodePath in geomNodeCollection:
    geomNode = nodePath.node()
    for i in range(geomNode.getNumGeoms()):
        geom = geomNode.getGeom(i)
        state = geomNode.getGeomState(i)
        print geom
        print state
        vdata = geom.getVertexData()
        print vdata

        vertex = GeomVertexReader(vdata, 'vertex')
        texcoord = GeomVertexReader(vdata, 'texcoord')
        while not vertex.isAtEnd():
            v = vertex.getData3f()
            # t = texcoord.getData2f()
            print "v = ", repr(v)


        for i in range(geom.getNumPrimitives()):
            prim = geom.getPrimitive(i)
            print prim
            vertex = GeomVertexReader(vdata, 'vertex')
             
            prim = prim.decompose()

            for p in range(prim.getNumPrimitives()):
                s = prim.getPrimitiveStart(p)
                e = prim.getPrimitiveEnd(p)
                for i in range(s, e):
                    vi = prim.getVertex(i)
                    vertex.setRow(vi)
                    v = vertex.getData3f()
                    print "prim %s has vertex %s: %s" % (p, vi, repr(v))