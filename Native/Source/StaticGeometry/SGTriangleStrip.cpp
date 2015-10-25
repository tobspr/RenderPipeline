
#include "SGTriangleStrip.h"


SGTriangleStrip::SGTriangleStrip() {

}

SGTriangleStrip::~SGTriangleStrip() {

}


void SGTriangleStrip::load_from_datagram(DatagramIterator &dgi) {
    size_t strip_size = dgi.get_uint32();

    // TODO: assert strip_size <= max_strip_size

    // Read in all triangles from the strip
    for (size_t k = 0; k < strip_size; ++k) {

        // Read in all vertices from the triangle
        for (size_t vtx = 0; vtx < 3; ++vtx) {

            // Position
            dgi.get_float32();
            dgi.get_float32();
            dgi.get_float32();
                
            // Normal
            dgi.get_float32();
            dgi.get_float32();
            dgi.get_float32();
                
            // UV
            dgi.get_float32();
            dgi.get_float32();
        }
    }
}


