
#include "SGDataset.h"


SGDataset::SGDataset() {
}


SGDataset::~SGDataset() {
}

void SGDataset::read_bounds(DatagramIterator &dgi) {
    _bb_min.set_x(dgi.get_float32());
    _bb_min.set_y(dgi.get_float32());
    _bb_min.set_z(dgi.get_float32());

    _bb_max.set_x(dgi.get_float32());
    _bb_max.set_y(dgi.get_float32());
    _bb_max.set_z(dgi.get_float32());
}

void SGDataset::attach_strip(const SGTriangleStrip *strip) {
    _strips.push_back(strip);
}

