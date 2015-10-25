#pragma once

#include "datagramIterator.h"


// This class handles a single triangle strip, which is part of a dataset
class SGTriangleStrip {

    public:
        SGTriangleStrip();
        ~SGTriangleStrip();

        void load_from_datagram(DatagramIterator &dgi);        

};
