/**
 * 
 * RenderPipeline
 * 
 * Copyright (c) 2014-2015 tobspr <tobias.springer1@gmail.com>
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 */


#include "SGDataset.h"
#include "SGTriangleStrip.h"

#include "common.h"

SGDataset::SGDataset() {
    _bounds = NULL;
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


void SGDataset::write_mappings(PTA_uchar data, int offset) {

    // Convert to an int array
    int *i_data = reinterpret_cast<int*>(data.p());

    int write_offs = (SG_MAX_DATASET_STRIPS+1) * offset;

    // Write the amount of strips
    i_data[write_offs++] = _strips.size();

    // Write the indices of all strips
    for (StripList::const_iterator iter = _strips.cbegin(); iter != _strips.cend(); ++iter) {
        i_data[write_offs++] = (*iter)->get_index();
    }
} 
