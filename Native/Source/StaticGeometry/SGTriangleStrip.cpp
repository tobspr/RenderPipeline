
#include "SGTriangleStrip.h"

#include "common.h"

SGTriangleStrip::SGTriangleStrip() {
    _index = -1;
    bb_min.set(0, 0, 0);
    bb_max.set(0, 0, 0);
}

SGTriangleStrip::~SGTriangleStrip() {

}


void SGTriangleStrip::load_from_datagram(DatagramIterator &dgi) {

    size_t strip_size = dgi.get_uint32();

    // TODO: assert strip_size <= max_strip_size

    // Reserve enough space
    _vertex_data.reserve(strip_size * 3);

    if (strip_size > SG_TRI_GROUP_SIZE) {
        cout << "ERROR: Strip size > " << SG_TRI_GROUP_SIZE << endl;
        return;
    }

    // Read bounding volume
    bb_min.set_x(dgi.get_float32());
    bb_min.set_y(dgi.get_float32());
    bb_min.set_z(dgi.get_float32());

    bb_max.set_x(dgi.get_float32());
    bb_max.set_y(dgi.get_float32());
    bb_max.set_z(dgi.get_float32());


    // Read in all triangles from the strip
    for (size_t k = 0; k < strip_size; ++k) {

        // Read in all vertices from the triangle
        for (size_t vtx = 0; vtx < 3; ++vtx) {

            PerVertexData vertex;

            // Position
            vertex.pos.set_x(dgi.get_float32());
            vertex.pos.set_y(dgi.get_float32());
            vertex.pos.set_z(dgi.get_float32());
                
            // Normal
            // vertex.normal.set_x(dgi.get_float32());
            // vertex.normal.set_y(dgi.get_float32());
            // vertex.normal.set_z(dgi.get_float32());
                
            // UV
            // vertex.uv.set_x(dgi.get_float32());
            // vertex.uv.set_y(dgi.get_float32());

            _vertex_data.push_back(vertex);
        }
    }
}


void SGTriangleStrip::write_to(PTA_uchar &data, int offset) {

    float* f_data = reinterpret_cast<float*>(data.p());

    // Compute the write offset:
    // 3 Triangles, each 4 floats:
    // Additionally increase the offset by 8 since we store the bounding volume too
    size_t write_offset = offset * (SG_TRI_GROUP_SIZE * 3 * 4 + 8);

    // Store our write position
    _index = offset;

    f_data[write_offset++] = bb_min.get_x();
    f_data[write_offset++] = bb_min.get_y();
    f_data[write_offset++] = bb_min.get_z();
    f_data[write_offset++] = 0;

    f_data[write_offset++] = bb_max.get_x();
    f_data[write_offset++] = bb_max.get_y();
    f_data[write_offset++] = bb_max.get_z();
    f_data[write_offset++] = 0;


    // Write all vertices
    for (size_t i = 0; i < _vertex_data.size(); ++i) {
        PerVertexData vertex = _vertex_data[i];

        f_data[write_offset++] = vertex.pos.get_x();
        f_data[write_offset++] = vertex.pos.get_y();
        f_data[write_offset++] = vertex.pos.get_z();

        f_data[write_offset++] = 0.0;
        // f_data[write_offset ++] = vertex.normal.get_x();
        // f_data[write_offset ++] = vertex.normal.get_y();
        // f_data[write_offset ++] = vertex.normal.get_z();

        // f_data[write_offset ++] = vertex.uv.get_x();
        // f_data[write_offset ++] = vertex.uv.get_y();
   }

   // Fill empty space with zeroes
   int fill_vertices = SG_TRI_GROUP_SIZE * 3 - _vertex_data.size();
   for (int i = 0; i < fill_vertices; ++i) {
        for (int k = 0; k < 4; ++k) {
            f_data[write_offset++] = 0.0;
        }  
   }
}

int SGTriangleStrip::get_index() const {
    return _index;
}
