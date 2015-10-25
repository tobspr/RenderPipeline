
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


    public:
      static TypeHandle get_class_type() {
        return _type_handle;
      }
      static void init_type() {
        PandaNode::init_type();
        register_type(_type_handle, "SGRenderNode", PandaNode::get_class_type());
      }
      virtual TypeHandle get_type() const {
        return get_class_type();
      }

    private:
      static TypeHandle _type_handle;
};
