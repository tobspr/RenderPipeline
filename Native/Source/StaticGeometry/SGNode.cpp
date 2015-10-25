

#include "SGNode.h"


SGNode::SGNode(const string &name, StaticGeometryHandler *handler,  int dataset) 
    : PandaNode(name) {

    _handler = handler;


}

SGNode::~SGNode() {
}