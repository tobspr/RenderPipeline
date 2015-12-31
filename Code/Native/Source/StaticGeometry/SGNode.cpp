/**
 * 
 * RenderPipeline
 * 
 * Copyright (c) 2014-2015 tobspr <tobias.springer1@gmail.com>
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 */



#include "SGNode.h"

#include "StaticGeometryHandler.h"
#include "SGDataset.h"

#include "cullTraverserData.h"
#include "cullTraverser.h"
#include "cullBinAttrib.h"


TypeHandle SGNode::_type_handle;

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
    set_final(true);
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
