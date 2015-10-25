#pragma once

#include "pandabase.h"
#include "pandaNode.h"

class StaticGeometryHandler;

// This class extends from pandanode and can be attached to the scene graph
// to be manipulated like a usual panda node, however, when rendering it it
// only attaches its triangle dataset to a list of rendered datasets instead
// of emitting geometry
class SGNode : public PandaNode {

    PUBLISHED:
        SGNode(const string &name, StaticGeometryHandler* handler, int dataset);
        ~SGNode();

    protected:

        StaticGeometryHandler *_handler;

};
