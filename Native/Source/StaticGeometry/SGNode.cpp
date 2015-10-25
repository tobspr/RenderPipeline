

#include "SGNode.h"

#include "StaticGeometryHandler.h"
#include "SGDataset.h"

#include "cullTraverserData.h"
#include "cullTraverser.h"
#include "cullBinAttrib.h"

SGNode::SGNode(const string &name, StaticGeometryHandler *handler,  int dataset_reference) 
    : PandaNode(name) {

    _handler = handler;
    _dataset_ref = dataset_reference;
    _dataset = _handler->get_dataset(dataset_reference);

    if (_dataset == NULL) {
        cout << "ERROR: No dataset with id " << dataset_reference << " found!" << endl;
        return;
    }

    set_internal_bounds(_dataset->get_bounds());
}

SGNode::~SGNode() {
}

bool SGNode::is_renderable() const {
  return true;
}

void SGNode::add_for_draw(CullTraverser *trav, CullTraverserData &data) {

    CPT(TransformState) internal_transform = data.get_internal_transform(trav);

    // TODO: Construct a correct matrix which contains the MVP of the node
    _handler->add_for_draw(_dataset_ref, get_transform()->get_mat());
}
