#pragma once


#include "pandabase.h"
#include "geom.h"
#include "geomPrimitive.h"
#include "geomVertexReader.h"
#include "pvector.h"

class MeshSplitter {

    private:
        MeshSplitter() {};
        ~MeshSplitter() {};

    public:
        struct Vertex {
            LVecBase3f pos;
            LVecBase3f normal;

            Vertex() {};
            Vertex(LVecBase3f c_pos, LVecBase3f c_nrm) : pos(c_pos), normal(c_nrm) {};
        };

        struct Triangle {
            Vertex vertices[3];
            LVecBase3f face_normal;
        };


    PUBLISHED:
        static void split_geom(CPT(Geom) geom);
        static bool triangle_intersects(const LVecBase3f &bb_min, const LVecBase3f &bb_max, Triangle* tri);


};
