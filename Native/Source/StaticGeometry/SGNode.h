#pragma once

#include "pandabase.h"
#include "pandaNode.h"

class StaticGeometryHandler;
class SGDataset;

// This class extends from pandanode and can be attached to the scene graph
// to be manipulated like a usual panda node, however, when rendering it it
// only attaches its triangle dataset to a list of rendered datasets instead
// of emitting geometry
class SGNode : public PandaNode {

    PUBLISHED:
        SGNode(const string &name, StaticGeometryHandler* handler, int dataset_reference);
        ~SGNode();

    public:

        virtual void add_for_draw(CullTraverser *trav, CullTraverserData &data);
        virtual bool is_renderable() const;

    protected:

        StaticGeometryHandler *_handler;
        SGDataset* _dataset;
        int _dataset_ref;

};
