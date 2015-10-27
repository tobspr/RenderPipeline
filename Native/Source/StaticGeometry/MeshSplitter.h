#pragma once


#include "pandabase.h"
#include "geom.h"
#include "geomPrimitive.h"
#include "geomVertexReader.h"
#include "pvector.h"
#include "filename.h"

#include "common.h"


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

    public:

        static void read_triangles(CPT(Geom) geom, TriangleList &result);

        static bool triangle_intersects(const LVecBase3f &bb_min, const LVecBase3f &bb_max, Triangle* tri);
        static bool chunk_intersects(const LVecBase3f &bb_min_a, const LVecBase3f &bb_max_a, const LVecBase3f &bb_min_b, const LVecBase3f &bb_max_b);

        static void traverse_recursive(TriangleList &parent_triangles, const LVecBase3f bb_start, const LVecBase3f bb_end, TriangleResultList &results, int depth_left);
        static void find_minmax(const TriangleList &tris, LVecBase3f &bb_min, LVecBase3f &bb_max);

        static void optimize_results(TriangleResultList &results);

        static void find_common_vector(const Chunk* chunk, LVecBase3f &cvector, float& max_angle_diff);


        static void find_intersecting_chunks(const TriangleResultList &results, TriangleResultList &intersecting, const LVecBase3f &search_min, const LVecBase3f &search_max, int max_size = SG_TRI_GROUP_SIZE);
};



// This small class just wraps arround mesh splitter and handles the combining of geoms
// and the writing of the .rpsg files
class MeshSplitterWriter {

    PUBLISHED:
        MeshSplitterWriter();
        ~MeshSplitterWriter();

        void add_geom(CPT(Geom));
        void process(const Filename &dest);

    private:

        void write_results(const Filename &dest, const MeshSplitter::TriangleResultList &results, const LVecBase3f &bb_min, const LVecBase3f &bb_max);

        typedef list<CPT(Geom)> GeomList;

        GeomList _attached_geoms;
};

