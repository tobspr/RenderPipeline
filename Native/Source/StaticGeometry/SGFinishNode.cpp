

#include "SGFinishNode.h"

#include "omniBoundingVolume.h"
#include "cullBinAttrib.h"

SGFinishNode::SGFinishNode(StaticGeometryHandler *handler) : PandaNode("SGFinish") {
    _handler = handler;
    set_internal_bounds(new OmniBoundingVolume);
    set_final(true);
}


SGFinishNode::~SGFinishNode() {

}



bool SGFinishNode::is_renderable() const {
  return true;
}

void SGFinishNode::add_for_draw(CullTraverser *trav, CullTraverserData &data) {
    cout << "Finish draw" << endl;

}
