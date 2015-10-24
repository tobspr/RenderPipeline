#pragma once


#include "pandabase.h"
#include "geom.h"
#include "geomPrimitive.h"
#include "geomVertexReader.h"
#include "pvector.h"

#define TRI_GROUP_SIZE 1024


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


    typedef list<Triangle*> TriangleList;
    typedef vector<TriangleList> TriangleResultList;



    PUBLISHED:
        static void split_geom(CPT(Geom) geom);
        static bool triangle_intersects(const LVecBase3f &bb_min, const LVecBase3f &bb_max, Triangle* tri);

    private:
        static void traverse_recursive(TriangleList &parent_triangles, const LVecBase3f bb_start, const LVecBase3f bb_end, TriangleResultList &results, int depth_left);

};
