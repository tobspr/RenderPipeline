
#include "SGDataset.h"
#include "SGTriangleStrip.h"

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
    if (_strips.size() >= 1023) {
        cout << "ERROR! Dataset cannot store more than 1023 strips" << endl;
        return;
    }
    _strips.push_back(strip);
}


PT(BoundingBox) SGDataset::get_bounds() {
    return _bounds;
}


void SGDataset::write_mappings(PTA_uchar data, int offset) {

    // Convert to an int array
    int *i_data = reinterpret_cast<int*>(data.p());

    int write_offs = 1024 * offset;

    // Write the amount of strips
    i_data[write_offs++] = _strips.size();

    // Write the indices of all strips
    for (StripList::const_iterator iter = _strips.cbegin(); iter != _strips.cend(); ++iter) {
        i_data[write_offs++] = (*iter)->get_index();
    }

    cout << "Wrote mappings up to " << write_offs << endl; 
}    
