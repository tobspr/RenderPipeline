

#include "SGRenderNode.h"

#include "omniBoundingVolume.h"
#include "cullBinAttrib.h"

SGRenderNode::SGRenderNode(StaticGeometryHandler *handler) : PandaNode("SGRender") {
    _handler = handler;
    set_internal_bounds(new OmniBoundingVolume);
    set_final(true);
}


SGRenderNode::~SGRenderNode() {

}



bool SGRenderNode::is_renderable() const {
  return true;
}

void SGRenderNode::add_for_draw(CullTraverser *trav, CullTraverserData &data) {
    cout << "Finish draw" << endl;
    
}
