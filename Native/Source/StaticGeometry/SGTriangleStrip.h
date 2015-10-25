#pragma once

#include "datagramIterator.h"
#include "luse.h"

// This class handles a single triangle strip, which is part of a dataset
class SGTriangleStrip {

    public:
        SGTriangleStrip();
        ~SGTriangleStrip();

        void load_from_datagram(DatagramIterator &dgi);
        void write_to(PTA_uchar &data, int offset);

        int get_index() const;

    private:

        struct PerVertexData {
            LVecBase3f pos;
            LVecBase3f normal;
            LVecBase2f uv;
        };

        int _index;

        vector<PerVertexData> _vertex_data;

};
