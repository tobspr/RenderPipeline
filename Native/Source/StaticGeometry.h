#pragma once


#include "pandabase.h"
#include "datagramIterator.h"
#include <list>


// This class handles a single triangle strip, which is part of a dataset
class SGTriangleStrip {

    public:
        SGTriangleStrip();
        ~SGTriangleStrip();

        void load_from_datagram(DatagramIterator &dgi);        

};


// This class contains a whole dataset of triangle strips
class SGDataset {

    public:
        SGDataset();
        ~SGDataset();

        void attach_strip(const SGTriangleStrip *strip);

    private:

        list<const SGTriangleStrip*> _strips;

};


// This class extends from pandanode and can be attached to the scene graph
// to be manipulated like a usual panda node, however, when rendering it it
// only attaches its triangle dataset to a list of rendered datasets instead
// of emitting geometry
class SGNode {

};