
#pragma once

#include "pandabase.h"
#include "pandaNode.h"
#include "renderState.h"

class StaticGeometryHandler;

// This node is attached to the scene graph and called last, it renders all
// static geometry to a buffer
class SGRenderNode : public PandaNode {

    PUBLISHED:
        SGRenderNode(StaticGeometryHandler* handler);
        ~SGRenderNode();

    public:

        virtual void add_for_draw(CullTraverser *trav, CullTraverserData &data);
        virtual bool is_renderable() const;

        
    private:

        void create_default_geom();

        StaticGeometryHandler* _handler;
        PT(Geom) _geom_strip;
        CPT(RenderState) _base_render_state;
};
