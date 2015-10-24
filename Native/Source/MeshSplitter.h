#pragma once


#include "pandabase.h"
#include "geom.h"
#include "geomPrimitive.h"
#include "geomVertexReader.h"
#include "pvector.h"
#include "filename.h"

#define TRI_GROUP_SIZE 1024


class MeshSplitter {

    private:
        MeshSplitter() {};
        ~MeshSplitter() {};

    public:
        struct Vertex {
            LVecBase3f pos;
            LVecBase3f normal;
            LVecBase2f uv;

            Vertex() {};
            Vertex(const LVecBase3f &c_pos, const LVecBase3f &c_nrm, const LVecBase2f &c_uv) 
                : pos(c_pos), normal(c_nrm), uv(c_uv) {};
        };

        struct Triangle {
            Vertex vertices[3];
            LVecBase3f face_normal;
        };


        typedef list<Triangle*> TriangleList;

        struct Chunk {
            TriangleList triangles;
            LVecBase3f bb_min;
            LVecBase3f bb_max;
        };

        typedef list<Chunk*> TriangleResultList;


    PUBLISHED:

        static void split_geom(CPT(Geom) geom, const Filename &dest, bool append = false);

    private:

        static void write_results(const TriangleResultList &results, const Filename &dest, bool append);

        static bool triangle_intersects(const LVecBase3f &bb_min, const LVecBase3f &bb_max, Triangle* tri);
        static bool chunk_intersects(const LVecBase3f &bb_min_a, const LVecBase3f &bb_max_a, const LVecBase3f &bb_min_b, const LVecBase3f &bb_max_b);

        static void traverse_recursive(TriangleList &parent_triangles, const LVecBase3f bb_start, const LVecBase3f bb_end, TriangleResultList &results, int depth_left);
        static void find_minmax(const TriangleList &tris, LVecBase3f &bb_min, LVecBase3f &bb_max);

        static void read_triangles(CPT(Geom) geom, TriangleList &result);
        static void optimize_results(TriangleResultList &results);

        static void find_intersecting_chunks(const TriangleResultList &results, TriangleResultList &intersecting, const LVecBase3f &search_min, const LVecBase3f &search_max, int max_size = TRI_GROUP_SIZE);
};

