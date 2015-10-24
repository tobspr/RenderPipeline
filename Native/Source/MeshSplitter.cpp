

#include "MeshSplitter.h"

#include <limits.h>


void MeshSplitter::split_geom(CPT(Geom) geom) {
    cout << "Splitting geom .." << endl;

    // Create a vertex reader to simplify the reading of positions
    CPT(GeomVertexData) vertex_data = geom->get_vertex_data();
    GeomVertexReader vertex_reader(vertex_data, "vertex");
    GeomVertexReader normal_reader(vertex_data, "normal");

    TriangleList all_triangles;

    // Collect all triangles
    for (int prim_idx = 0; prim_idx < geom->get_num_primitives(); ++prim_idx) {
        CPT(GeomPrimitive) primitive = geom->get_primitive(prim_idx);

        // TODO: Check if the GeomPrimitive is a GeomTriangles, otherwise skip it

        // Iterate over all Primitives (=Triangles) of that GeomPrimitive
        for (int tri_idx = 0; tri_idx < primitive->get_num_primitives(); ++tri_idx) {

            int tri_start = primitive->get_primitive_start(tri_idx);
            int tri_end = primitive->get_primitive_end(tri_idx);
            Triangle* tri = new Triangle();

            // Iterate over the Vertices of that Triangle
            for (int vtx_idx = tri_start, offs=0; vtx_idx < tri_end; ++vtx_idx, ++offs) {
                int vtx_mapped = primitive->get_vertex(vtx_idx);
                vertex_reader.set_row(vtx_mapped);
                normal_reader.set_row(vtx_mapped);
                LVecBase3 vtx_pos = vertex_reader.get_data3f();
                LVecBase3 vtx_nrm = normal_reader.get_data3f();

                // TODO: The vertex position might be in model space. Convert it to
                // world space first

                tri->vertices[offs] = Vertex(vtx_pos, vtx_nrm);
            }

            // Compute the triangle normal
            LVecBase3 v0 = tri->vertices[1].pos - tri->vertices[0].pos;
            LVecBase3 v1 = tri->vertices[2].pos - tri->vertices[0].pos;

            LVecBase3 face_normal = v0.cross(v1);

            // Make sure the normal points into the right direction, compute
            // the dot product between the normal of the first vertex and the
            // face, if it is negative, we have to swap the normal
            float fv_dot = tri->vertices[0].normal.dot(face_normal);
            tri->face_normal = fv_dot >= 0.0 ? face_normal : face_normal; 

            all_triangles.push_back(tri);
           
        }
    } 

    // Early exit?
    if (all_triangles.size() < 1) {
        cout << "Empty geom!" << endl;
        return;
    }

    // Find a bounding box enclosing all triangles
    float min_x = FLT_MAX, min_y = FLT_MAX, min_z = FLT_MAX;
    float max_x = FLT_MIN, max_y = FLT_MIN, max_z = FLT_MIN;
    for (TriangleList::iterator start = all_triangles.begin(); start != all_triangles.end(); ++start) {
        Triangle *tri = *start;
        for (int vtx_idx = 0; vtx_idx < 3; ++vtx_idx) {
            min_x = min(min_x, tri->vertices[vtx_idx].pos.get_x());
            min_y = min(min_y, tri->vertices[vtx_idx].pos.get_y());
            min_z = min(min_z, tri->vertices[vtx_idx].pos.get_z());

            max_x = max(max_x, tri->vertices[vtx_idx].pos.get_x());
            max_y = max(max_y, tri->vertices[vtx_idx].pos.get_y());
            max_z = max(max_z, tri->vertices[vtx_idx].pos.get_z());
        }
    }

    const float b_bias = 0.0;

    // Increase bounding volume a bit
    min_x -= b_bias;
    min_y -= b_bias;
    min_z -= b_bias;

    max_x += b_bias;
    max_y += b_bias;
    max_z += b_bias;

    cout << "Found " << all_triangles.size() << " triangles .." << endl;
    cout << "Bounding box is from (" << min_x << "," << min_y << "," << min_z 
         << ") to (" << max_x << "," << max_y << "," << max_z << ")" << endl;


    LVecBase3 bb_start(min_x, min_y, min_z);
    LVecBase3 bb_end(max_x, max_y, max_z);



    int num_not_intersecting = 0;

    // This is just for testing and safety purposes. It checks if all triangles
    // are inside the computed bounding box.
    for (TriangleList::iterator start = all_triangles.begin(); start != all_triangles.end(); ++start) {
        Triangle *tri = *start;
        if (!triangle_intersects(bb_start, bb_end, tri)) {
            // cout << "  ERROR! Triangle does not intersect object bounding box?" << endl;
            num_not_intersecting ++;
        }
    }

    cout << "Not intersecting triangles: " << num_not_intersecting << " out of " << all_triangles.size() << endl;

    cout << "Traversing recursive ..." << endl;
    TriangleResultList results;

    traverse_recursive(all_triangles, bb_start, bb_end, results, 10);

    cout << "Found " << results.size() << " Strips! This is an effective count of " << results.size() * TRI_GROUP_SIZE << " triangles" << endl;

    // Write results
    cout << "Writing out model file .." << endl;
    ofstream outp("model.rpsg");

    for (int result_idx = 0; result_idx < results.size(); ++result_idx) {

        for (TriangleList::iterator start = results[result_idx].begin(); start != results[result_idx].end(); ++start) {
            Triangle *tri = *start;
            for (int i = 0; i < 3; ++i) {
                outp << tri->vertices[i].pos.get_x() << ",";
                outp << tri->vertices[i].pos.get_y() << ",";
                outp << tri->vertices[i].pos.get_z() << "/";
            }
            outp << "|";
        }

        outp << endl;
    }


    outp.close();


    // TODO: Delete all triangles from all_triangles, since they are not reference counted.

}


void MeshSplitter::traverse_recursive(TriangleList &parent_triangles, const LVecBase3f bb_start, const LVecBase3f bb_end, TriangleResultList &results, int depth_left) {
    
    if (depth_left < 0) {
        // cout << "Max depth reached! Could not split mesh further" << endl;
        return;
    } 

    // Create a vector to store all triangles which match
    TriangleList matching_triangle_list;

    // Assuming an even distribution, we will match about 1 / 8 of the parent triangles
    // matching_triangles.reserve(parent_triangles.size() / 8);

    // Intersect triangles
    for (TriangleList::iterator start = parent_triangles.begin(); start != parent_triangles.end(); ++start) {
        Triangle *tri = *start;
        if (triangle_intersects(bb_start, bb_end, tri)) {
            matching_triangle_list.push_back(tri);
        }
    }


   // cout << "Checking chunk .. from " << parent_triangles.size() << " intersected " << matching_triangles.size() << endl;

    // If we hit no triangles, just stop
    if (matching_triangle_list.size() == 0) {
        return;
    }

    // If we hit less than n triangles, we can create a strip and stop traversing
    if (matching_triangle_list.size() <= TRI_GROUP_SIZE) {
        // cout << "Stop traversing! Create chunk of size " << matching_triangles.size() << " (parent had " << parent_triangles.size() << ")" << endl;
        // results.push_back(matching_triangles);

        // for (int i = 0 < matching_triangle_list.size(); ++i) {
            // parent_triangles.remove(matching_triangle_list[i]);
        // }
        // Take all matches from the pool
        for (TriangleList::iterator start = matching_triangle_list.begin(); start != matching_triangle_list.end(); ++start) {
            parent_triangles.remove(*start);
        }

        results.push_back(matching_triangle_list);

        return;
    }

    //cout << "Split chunk:" << endl;
    //cout << "From " << bb_start << " to " << bb_end << " == " << matching_triangles.size() << endl;

    LVecBase3f half_size = (bb_end - bb_start) / 2.0;

    // Otherwise we split the chunk in eight smaller chunks
    for (int x = 0; x < 2; ++x) {
        
        if (x != 0 && half_size.get_x() < 0.0001) continue;
        
        for (int y = 0; y < 2; ++y) {

            if (y != 0 && half_size.get_y() < 0.0001) continue;
        
            for (int z = 0; z < 2; ++z) {

                if (z != 0 && half_size.get_z() < 0.0001) continue;

                LVecBase3f chunk_start(
                    bb_start.get_x() + x * half_size.get_x(),
                    bb_start.get_y() + y * half_size.get_y(),
                    bb_start.get_z() + z * half_size.get_z()
                );
                //cout << " -> " << chunk_start << " / " << chunk_start + half_size << endl;
                traverse_recursive(matching_triangle_list, chunk_start, chunk_start + half_size, results, depth_left - 1);
            }
        }
    }

    // traverse_recursive(matching_triangles, LVecBase3f(), LVecBase3f());



}



// Inspired from
// http://stackoverflow.com/questions/17458562/efficient-aabb-triangle-intersection-in-c-sharp

inline LVecBase3f get_box_normal(int idx) {
    return LVecBase3f(
        idx == 0 ? 1.0 : 0.0,
        idx == 1 ? 1.0 : 0.0,
        idx == 2 ? 1.0 : 0.0);
}

inline void project(const LVecBase3f &axis, const LVecBase3f &vertex, float &minval, float &maxval) {
    float val = axis.dot(vertex);
    if (val < minval) minval = val;
    if (val > maxval) maxval = val;
}


inline void project_triangle(MeshSplitter::Triangle* tri, const LVecBase3f &axis, float &minval, float &maxval) {
    minval = FLT_MAX;
    maxval = FLT_MIN;
    for (int vtx = 0; vtx < 3; ++vtx) {
        project(axis, tri->vertices[vtx].pos, minval, maxval);
    }
}


void project_box(const LVecBase3f &bb_min, const LVecBase3f &bb_max, const LVecBase3f &axis, float &minval, float &maxval) {
    minval = FLT_MAX;
    maxval = FLT_MIN;

    // Lower side of the box
    project(axis, LVecBase3f(bb_min.get_x(), bb_min.get_y(), bb_min.get_z()), minval, maxval);
    project(axis, LVecBase3f(bb_max.get_x(), bb_min.get_y(), bb_min.get_z()), minval, maxval);
    project(axis, LVecBase3f(bb_min.get_x(), bb_max.get_y(), bb_min.get_z()), minval, maxval);
    project(axis, LVecBase3f(bb_max.get_x(), bb_max.get_y(), bb_min.get_z()), minval, maxval);

    // Upper side of the box
    project(axis, LVecBase3f(bb_min.get_x(), bb_min.get_y(), bb_max.get_z()), minval, maxval);
    project(axis, LVecBase3f(bb_max.get_x(), bb_min.get_y(), bb_max.get_z()), minval, maxval);
    project(axis, LVecBase3f(bb_min.get_x(), bb_max.get_y(), bb_max.get_z()), minval, maxval);
    project(axis, LVecBase3f(bb_max.get_x(), bb_max.get_y(), bb_max.get_z()), minval, maxval);

}

bool MeshSplitter::triangle_intersects(const LVecBase3f &bb_min, const LVecBase3f &bb_max, Triangle* tri) {

    float tri_min = 0, tri_max = 0;
    float box_min = 0, box_max = 0;

    // Test box normals (x, y, and z)
    for (int i = 0; i < 3; ++i) {
        LVecBase3f normal = get_box_normal(i);
        project_triangle(tri, normal, tri_min, tri_max);

        // No intersection, since the point was not in the box
        if (tri_max < bb_min[i] || tri_min >= bb_max[i])
            return false;
    }

    // Check for a correct normal
    double tri_offs = tri->face_normal.dot(tri->vertices[0].pos);
    project_box(bb_min, bb_max, tri->face_normal, box_min, box_max);
    if (box_max < tri_offs || box_min > tri_offs)
        return false;

    // Test the edge cross products
    LVecBase3f tri_edges[3] = {
        tri->vertices[0].pos - tri->vertices[1].pos,
        tri->vertices[0].pos - tri->vertices[2].pos,
        tri->vertices[0].pos - tri->vertices[0].pos,
    };

    for (int i = 0; i < 3; ++i) {
        for (int j = 0; j < 3; ++j) {

            LVecBase3f axis = tri_edges[i].cross(get_box_normal(j));
            project_box(bb_min, bb_max, axis, box_min, box_max);
            project_triangle(tri, axis, tri_min, tri_max);
            if (box_max <= tri_min || box_min >= tri_max)
                return false;
        }
    }

    return true;


}
