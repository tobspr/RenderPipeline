

#include "MeshSplitter.h"

#include <limits.h>
#include <algorithm>

#include "datagram.h"


void MeshSplitter::split_geom(CPT(Geom) geom, const Filename &dest, bool append) {


    cout << "Reading in geometry .." << endl;
    TriangleList all_triangles;
    read_triangles(geom, all_triangles);

    cout << "Read in " << all_triangles.size() << " triangles." << endl;

    // Early exit?
    if (all_triangles.size() < 1) {
        cout << "Empty geom!" << endl;
        return;
    }


    cout << "Finding bounding volume .." << endl;
    LVecBase3f bb_start, bb_end;
    find_minmax(all_triangles, bb_start, bb_end);


    cout << "Traversing recursive to find chunks of size " << TRI_GROUP_SIZE << " ..." << endl;
    TriangleResultList results;

    traverse_recursive(all_triangles, bb_start, bb_end, results, 10);

    cout << "Found " << results.size() << " Strips! This is an effective count of " << results.size() * TRI_GROUP_SIZE << " triangles" << endl;

    cout << "Optimizing results and merging small chunks .. " << endl;
    optimize_results(results);

    cout << "Optimized version has " << results.size() << " Strips! This is an effective count of " << results.size() * TRI_GROUP_SIZE << " triangles" << endl;


    // Write results
    cout << "Writing out model file .." << endl;
    ofstream outp(dest.get_fullpath(), ios_base::app);

    Datagram dg;

    dg.add_string("RPSG");
    dg.add_uint32(results.size());

    for (TriangleResultList::iterator rstart = results.begin(); rstart != results.end(); ++rstart) {

        dg.add_uint32((*rstart)->triangles.size());

        for (TriangleList::iterator start = (*rstart)->triangles.begin(); start != (*rstart)->triangles.end(); ++start) {
            Triangle *tri = *start;
            for (int i = 0; i < 3; ++i) {
                dg.add_float32(tri->vertices[i].pos.get_x());
                dg.add_float32(tri->vertices[i].pos.get_y());
                dg.add_float32(tri->vertices[i].pos.get_z());
                dg.add_float32(tri->vertices[i].normal.get_x());
                dg.add_float32(tri->vertices[i].normal.get_y());
                dg.add_float32(tri->vertices[i].normal.get_z());
                dg.add_float32(tri->vertices[i].uv.get_x());
                dg.add_float32(tri->vertices[i].uv.get_y());
            }
        }
    }

    // dg.write(outp);
    outp << dg.get_message();

    outp.close();

    // TODO: Delete all triangles
    // TODO: Delete all chunks

}


void MeshSplitter::read_triangles(CPT(Geom) geom, TriangleList &result) {

    // Create a vertex reader to simplify the reading of positions
    CPT(GeomVertexData) vertex_data = geom->get_vertex_data();
    GeomVertexReader vertex_reader(vertex_data, "vertex");
    GeomVertexReader normal_reader(vertex_data, "normal");
    GeomVertexReader uv_reader(vertex_data, "texcoord");

    if (!uv_reader.has_column()) {
        cout << "ERROR: Mesh has no uv coordinates assigned!" << endl;
        return;
    }


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
                LVecBase3f vtx_pos = vertex_reader.get_data3f();
                LVecBase3f vtx_nrm = normal_reader.get_data3f();
                LVecBase2f vtx_uv = uv_reader.get_data2f();

                // TODO: The vertex position might be in model space. Convert it to
                // world space first
                tri->vertices[offs] = Vertex(vtx_pos, vtx_nrm, vtx_uv);
            }

            // Compute the triangle normal
            LVecBase3f v0 = tri->vertices[1].pos - tri->vertices[0].pos;
            LVecBase3f v1 = tri->vertices[2].pos - tri->vertices[0].pos;

            LVecBase3f face_normal = v0.cross(v1);

            // Make sure the normal points into the right direction, compute
            // the dot product between the normal of the first vertex and the
            // face, if it is negative, we have to swap the normal
            float fv_dot = tri->vertices[0].normal.dot(face_normal);
            tri->face_normal = fv_dot >= 0.0 ? face_normal : -face_normal;
            result.push_back(tri);
        }
    } 
}



void MeshSplitter::find_minmax(TriangleList tris, LVecBase3f &bb_min, LVecBase3f &bb_max) {

    // Find a bounding box enclosing all triangles
    float min_x = FLT_MAX, min_y = FLT_MAX, min_z = FLT_MAX;
    float max_x = FLT_MIN, max_y = FLT_MIN, max_z = FLT_MIN;
    for (TriangleList::iterator start = tris.begin(); start != tris.end(); ++start) {
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

    // Increase bounding volume by a small bias
    min_x -= b_bias;
    min_y -= b_bias;
    min_z -= b_bias;

    max_x += b_bias;
    max_y += b_bias;
    max_z += b_bias;

    bb_min = LVecBase3f(min_x, min_y, min_z);
    bb_max = LVecBase3f(max_x, max_y, max_z);
}


bool compare_chunk_size(MeshSplitter::Chunk* a, MeshSplitter::Chunk* b) {
    return a->triangles.size() < b->triangles.size();
}

void MeshSplitter::optimize_results(TriangleResultList &results) {

    // Chunks which are filled up to certain percentage are ok
    int size_ok = TRI_GROUP_SIZE * 0.9;


    int num_optimization = 10000;

    // Perform the optimization several times
    while (num_optimization --> 0) {

        // Iterate over all chunks
        for(TriangleResultList::iterator iter = results.begin(); iter != results.end(); ++iter) {

            Chunk* current_chunk = *iter;

            // Check if the chunk is not satisfying
            if(current_chunk->triangles.size() < size_ok) {

                // Get the area arround the chunk
                LVecBase3f search_min = current_chunk->bb_min;
                LVecBase3f search_max = current_chunk->bb_max;

                // Increase the area twice by its size, to get the search radius
                LVecBase3f bb_size = (search_max - search_min);
                search_min -= bb_size * 2.0;
                search_max += bb_size * 2.0;

                // Find all intersecting chunks where this chunk could be merged with
                TriangleResultList intersecting;
                find_intersecting_chunks(results, intersecting, search_min, search_max, TRI_GROUP_SIZE - current_chunk->triangles.size());
                
                // Remove our current chunk from the list of surrounding chunks
                intersecting.remove(current_chunk);

                if (intersecting.size() < 1) {
                    // Bad ... no neighbours, can't optimize it
                    continue;
                } 

                // Find chunk with the smallest size from the neighbours
                Chunk* closest = *max_element(intersecting.begin(), intersecting.end(), compare_chunk_size);

                /*
                // Find closest chunk
                LVecBase3f chunk_mid = (current_chunk->bb_min + current_chunk->bb_max) * 0.5;
                Chunk *closest = nullptr;
                float closest_dist = FLT_MAX;
                for (TriangleResultList::iterator siter = intersecting.begin(); siter != intersecting.end(); ++siter) {
                    float dist = (((*siter)->bb_min + (*iter)->bb_max) * 0.5 - chunk_mid).length_squared();
                    if (dist < closest_dist) {
                        closest_dist = dist;
                        closest = *siter;
                    }
                }

                // This should be always true
                assert(closest != nullptr);

                */

                // Merge chunks
                closest->triangles.splice(closest->triangles.begin(), current_chunk->triangles);
                results.remove(current_chunk);


                // Update bounding box
                find_minmax(closest->triangles, closest->bb_min, closest->bb_max);

                // We have to break here, since our iterator is most likely invalid now
                break;
            }
        }

    }

}



void MeshSplitter::traverse_recursive(TriangleList &parent_triangles, const LVecBase3f bb_start, const LVecBase3f bb_end, TriangleResultList &results, int depth_left) {
    
    if (depth_left < 0) {
        // cout << "Max depth reached! Could not split mesh further" << endl;
        return;
    } 

    // Create a vector to store all triangles which match
    TriangleList matching_triangle_list;

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

        // Take all matches from the pool
        for (TriangleList::iterator start = matching_triangle_list.begin(); start != matching_triangle_list.end(); ++start) {
            parent_triangles.remove(*start);
        }

        // Construct a new chunk
        Chunk* chunk = new Chunk();
        chunk->triangles = matching_triangle_list;
        find_minmax(chunk->triangles, chunk->bb_min, chunk->bb_max);

        results.push_back(chunk);

        return;
    }


    LVecBase3f half_size = (bb_end - bb_start) / 2.0;

    // Otherwise we split the chunk in eight smaller chunks.
    // If we have a "flat" octree in one dimension, we treat it as a quadtree.
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
                traverse_recursive(matching_triangle_list, chunk_start, chunk_start + half_size, results, depth_left - 1);
            }
        }
    }
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
    minval = 1000000.0;
    maxval = -1000000.0;
    for (int vtx = 0; vtx < 3; ++vtx) {
        project(axis, tri->vertices[vtx].pos, minval, maxval);
    }
}


void project_box(const LVecBase3f &bb_min, const LVecBase3f &bb_max, const LVecBase3f &axis, float &minval, float &maxval) {
    minval = 1000000.0;
    maxval = -1000000.0;

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
        LVecBase3f box_normal = get_box_normal(i);
        project_triangle(tri, box_normal, tri_min, tri_max);

        // No intersection, since the point was not in the box
        if (tri_max < bb_min[i] || tri_min > bb_max[i]) {
            return false;
        }
    }

    // Check for triangle normal
    double tri_offs = tri->face_normal.dot(tri->vertices[0].pos);
    project_box(bb_min, bb_max, tri->face_normal, box_min, box_max);
    if (box_max < tri_offs || box_min > tri_offs)
        return false;

    // Test the edge cross products
    LVecBase3f tri_edges[3] = {
        tri->vertices[0].pos - tri->vertices[1].pos,
        tri->vertices[1].pos - tri->vertices[2].pos,
        tri->vertices[2].pos - tri->vertices[0].pos,
    };

    for (int i = 0; i < 3; ++i) {        
        for (int j = 0; j < 3; ++j) {
            LVecBase3f axis = tri_edges[i].cross(get_box_normal(j));
            project_box(bb_min, bb_max, axis, box_min, box_max);
            project_triangle(tri, axis, tri_min, tri_max);

            if (box_max < tri_min || box_min > tri_max) {
                return false;
            }
        }
    }

    return true;
}

bool MeshSplitter::chunk_intersects(const LVecBase3f &a_min, const LVecBase3f &a_max, const LVecBase3f &b_min, const LVecBase3f &b_max) {

    if (a_max.get_x() < b_min.get_x()) return false; // a is left of b
    if (a_min.get_x() > b_max.get_x()) return false; // a is right of b
    if (a_max.get_y() < b_min.get_y()) return false; // a is above b
    if (a_min.get_y() > b_max.get_y()) return false; // a is below b
    if (a_max.get_z() < b_min.get_z()) return false; // a is behind b
    if (a_min.get_z() > b_max.get_z()) return false; // a is infront of b

    return true;
}

// When max size is set, only chunks with a size <= max_size are returned
void MeshSplitter::find_intersecting_chunks(TriangleResultList &results, TriangleResultList &intersecting,
    const LVecBase3f &search_min, const LVecBase3f &search_max, int max_size) {
    for(TriangleResultList::iterator iter = results.begin(); iter != results.end(); ++iter) {
        if (chunk_intersects(search_min, search_max, (*iter)->bb_min, (*iter)->bb_max)) {
            if ((*iter)->triangles.size() <= max_size) {
                intersecting.push_back(*iter);
            }
        }
    }
}
