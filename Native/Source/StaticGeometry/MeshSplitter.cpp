

#include "MeshSplitter.h"

#include <limits.h>
#include <algorithm>

#include "datagram.h"


void MeshSplitter::read_triangles(CPT(Geom) geom, TriangleList &result) {

    // Create a vertex reader to simplify the reading of positions
    CPT(GeomVertexData) vertex_data = geom->get_vertex_data();
    GeomVertexReader vertex_reader(vertex_data, "vertex");
    GeomVertexReader normal_reader(vertex_data, "normal");
    GeomVertexReader uv_reader(vertex_data, "texcoord");

    bool has_uv = uv_reader.has_column();

    if (!normal_reader.has_column()) {
        cout << "ERROR: Mesh has no stored normals!" << endl;
        return;
    }

    if (!has_uv) {
        cout << "WARNING: Mesh has no uv coordinates assigned!" << endl;
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
                uv_reader.set_row(vtx_mapped);
                LVecBase3f vtx_pos = vertex_reader.get_data3f();
                LVecBase3f vtx_nrm = normal_reader.get_data3f();
                LVecBase2f vtx_uv(0);

                if (has_uv) {
                    vtx_uv = uv_reader.get_data2f();
                }
                
                // TODO: The vertex position might be in model space. Convert it to
                // world space first
                tri->vertices[offs] = Vertex(vtx_pos, vtx_nrm, vtx_uv);
            }

            // Compute the triangle normal
            LVecBase3f v0 = tri->vertices[1].pos - tri->vertices[0].pos;
            LVecBase3f v1 = tri->vertices[2].pos - tri->vertices[0].pos;

            LVecBase3f face_normal = v0.cross(v1);
            face_normal.normalize();

            // Make sure the normal points into the right direction, compute
            // the dot product between the normal of the first vertex and the
            // face, if it is negative, we have to swap the normal
            float fv_dot = tri->vertices[0].normal.dot(face_normal);
            tri->face_normal = fv_dot >= 0.0 ? face_normal : -face_normal;
            result.push_back(tri);
        }
    } 
}



void MeshSplitter::find_minmax(const TriangleList &tris, LVecBase3f &bb_min, LVecBase3f &bb_max) {

    // Find a bounding box enclosing all triangles
    float min_x = FLT_MAX, min_y = FLT_MAX, min_z = FLT_MAX;
    float max_x = FLT_MIN, max_y = FLT_MIN, max_z = FLT_MIN;
    for (TriangleList::const_iterator start = tris.cbegin(); start != tris.cend(); ++start) {
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

    bb_min.set(min_x, min_y, min_z);
    bb_max.set(max_x, max_y, max_z);
}



void MeshSplitter::optimize_results(TriangleResultList &results) {

    // Chunks which are filled up to certain percentage are ok
    int size_ok = SG_TRI_GROUP_SIZE * 0.8;


    int num_optimization = 50000;

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
                search_min -= bb_size * 0.5;
                search_max += bb_size * 0.5;

                // Find all intersecting chunks where this chunk could be merged with
                TriangleResultList intersecting;
                find_intersecting_chunks(results, intersecting, search_min, search_max, SG_TRI_GROUP_SIZE - current_chunk->triangles.size());
                
                // Remove our current chunk from the list of surrounding chunks
                intersecting.remove(current_chunk);

                if (intersecting.size() < 1) {
                    // Bad ... no neighbours, can't optimize it
                    continue;
                } 

                // Find chunk with the smallest size from the neighbours
                //Chunk* closest = *max_element(intersecting.begin(), intersecting.end(), current_chunk->compare_common_vec);

                
                // Find chunk with the best fitting angle
                // LVecBase3f chunk_mid = (current_chunk->bb_min + current_chunk->bb_max) * 0.5;
                Chunk *closest = NULL;
                for (TriangleResultList::iterator siter = intersecting.begin(); siter != intersecting.end(); ++siter) {
                    if (closest == NULL || current_chunk->compare_common_vec(closest, *siter)) {
                        closest = *siter;
                    }
                }

                // This should be always true
                assert(closest != NULL);


                // Merge chunks
                closest->triangles.splice(closest->triangles.begin(), current_chunk->triangles);
                results.remove(current_chunk);


                // Update bounding box
                find_minmax(closest->triangles, closest->bb_min, closest->bb_max);
                find_common_vector(closest->triangles, closest->common_vector, closest->max_angle_diff);

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
    if (matching_triangle_list.size() <= SG_TRI_GROUP_SIZE) {

        // Take all matches from the pool
        for (TriangleList::iterator start = matching_triangle_list.begin(); start != matching_triangle_list.end(); ++start) {
            parent_triangles.remove(*start);
        }

        // Construct a new chunk
        Chunk* chunk = new Chunk();
        chunk->triangles = matching_triangle_list;
        find_minmax(chunk->triangles, chunk->bb_min, chunk->bb_max);
        find_common_vector(chunk->triangles, chunk->common_vector, chunk->max_angle_diff);

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
void MeshSplitter::find_intersecting_chunks(const TriangleResultList &results, TriangleResultList &intersecting,
    const LVecBase3f &search_min, const LVecBase3f &search_max, int max_size) {
    for(TriangleResultList::const_iterator iter = results.cbegin(); iter != results.cend(); ++iter) {
        if (chunk_intersects(search_min, search_max, (*iter)->bb_min, (*iter)->bb_max)) {
            if ((*iter)->triangles.size() <= max_size) {
                intersecting.push_back(*iter);
            }
        }
    }
}



void MeshSplitter::find_common_vector(const TriangleList &triangles, LVecBase3f &cvector, float& max_angle_diff) {

    const float PI = 3.14159265359;

    // First, average all vectors to get a common vector
    cvector.set(0, 0, 0);

    for(TriangleList::const_iterator iter = triangles.cbegin(); iter != triangles.cend(); ++iter) {
        cvector += (*iter)->face_normal;
    }

    cvector.normalize();

    max_angle_diff = -1000000.0;

    // Now, for each normal, check the angle between the face and the common vector,
    // and find the maximum 

    for(TriangleList::const_iterator iter = triangles.cbegin(); iter != triangles.cend(); ++iter) {
        float angle = acos((*iter)->face_normal.dot(cvector));
        if (angle < 0.0) angle += 2.0 * PI;

        if (angle > max_angle_diff) {
            max_angle_diff = angle;
         }
    }

    // cout << "Common vector is " << cvector << " and diff is " << max_angle_diff << endl;
}

MeshSplitterWriter::MeshSplitterWriter() {

}

MeshSplitterWriter::~MeshSplitterWriter() {

}

void MeshSplitterWriter::add_geom(CPT(Geom) geom) {
    _attached_geoms.push_back(geom);
}


void MeshSplitterWriter::process(const Filename &dest) {

    // Check for an empty writer
    if (_attached_geoms.size() < 1) {
        cout << "No geoms attached!" << endl;
        return;
    }

    // Construct a list to store all triangles
    MeshSplitter::TriangleList all_triangles;

    cout << "Reading in triangles ..." << endl;

    // Iterate over all geoms and collect their triangles
    for(GeomList::const_iterator iter = _attached_geoms.cbegin(); iter != _attached_geoms.cend(); ++iter) {
        CPT(Geom) geom = *iter;

        MeshSplitter::read_triangles(geom, all_triangles);
    }

    // Early exit?
    if (all_triangles.size() < 1) {
        cout << "Empty geom!" << endl;
        return;
    }

    cout << "Found " << all_triangles.size() << " triangles" << endl;

    cout << "Finding bounding volume .." << endl;
    LVecBase3f bb_start, bb_end;
    MeshSplitter::find_minmax(all_triangles, bb_start, bb_end);

    cout << "Traversing recursive to find chunks of size " << SG_TRI_GROUP_SIZE << " ..." << endl;
    MeshSplitter::TriangleResultList results;

    MeshSplitter::traverse_recursive(all_triangles, bb_start, bb_end, results, 15);
    cout << "Found " << results.size() << " Strips! This is an effective count of "
         << results.size() * SG_TRI_GROUP_SIZE << " triangles" << endl;
    cout << "Optimizing results and merging small chunks .. " << endl;
    MeshSplitter::optimize_results(results);

    cout << "Optimized version has " << results.size() << " Strips! This is an effective count of "
         << results.size() * SG_TRI_GROUP_SIZE << " triangles" << endl;
    cout << "Writing out model file .." << endl;
    
    write_results(dest, results, bb_start, bb_end);

}


void MeshSplitterWriter::write_results(const Filename &dest, const MeshSplitter::TriangleResultList &results, const LVecBase3f &bb_min, const LVecBase3f &bb_max) {
    Datagram dg;
    dg.add_fixed_string("RPSG", 4);


    // Write some format information
    dg.add_uint32(SG_TRI_GROUP_SIZE);


    dg.add_uint32(results.size());

    // Write model bounds
    dg.add_float32(bb_min.get_x());
    dg.add_float32(bb_min.get_y());
    dg.add_float32(bb_min.get_z());

    dg.add_float32(bb_max.get_x());
    dg.add_float32(bb_max.get_y());
    dg.add_float32(bb_max.get_z());

    for (MeshSplitter::TriangleResultList::const_iterator iter = results.cbegin(); iter != results.cend(); ++iter) {

        MeshSplitter::Chunk* chunk = *iter;

        // Make sure the minmax is still correct
        MeshSplitter::find_minmax(chunk->triangles, chunk->bb_min, chunk->bb_max);

        // Make sure the common vector is still correct
        MeshSplitter::find_common_vector(chunk->triangles, chunk->common_vector, chunk->max_angle_diff);

        dg.add_uint32(chunk->triangles.size());

        // Write chunk bounds
        dg.add_float32(chunk->bb_min.get_x());
        dg.add_float32(chunk->bb_min.get_y());
        dg.add_float32(chunk->bb_min.get_z());

        dg.add_float32(chunk->bb_max.get_x());
        dg.add_float32(chunk->bb_max.get_y());
        dg.add_float32(chunk->bb_max.get_z());

        // Write common vector
        dg.add_float32(chunk->common_vector.get_x());
        dg.add_float32(chunk->common_vector.get_y());
        dg.add_float32(chunk->common_vector.get_z());
        dg.add_float32(chunk->max_angle_diff);


        for (MeshSplitter::TriangleList::const_iterator start = chunk->triangles.cbegin(); start != chunk->triangles.cend(); ++start) {
            MeshSplitter::Triangle *tri = *start;
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

    std::ofstream outfile;
    outfile.open(dest.get_fullpath(), ios::out | ios::binary);
    outfile.write((char*)dg.get_data(), dg.get_length());
    outfile.close();
}