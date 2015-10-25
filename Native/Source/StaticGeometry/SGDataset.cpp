
#include "SGDataset.h"


SGDataset::SGDataset() {
    _bounds = nullptr;
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

    _bounds = new BoundingBox(_bb_min, _bb_max);
}

void SGDataset::attach_strip(const SGTriangleStrip *strip) {
    _strips.push_back(strip);
}


PT(BoundingBox) SGDataset::get_bounds() {
    return _bounds;
}

