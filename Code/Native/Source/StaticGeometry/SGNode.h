/**
 * 
 * RenderPipeline
 * 
 * Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>
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


    public:
      static TypeHandle get_class_type() {
        return _type_handle;
      }
      static void init_type() {
        PandaNode::init_type();
        register_type(_type_handle, "SGNode", PandaNode::get_class_type());
      }
      virtual TypeHandle get_type() const {
        return get_class_type();
      }

    private:
      static TypeHandle _type_handle;

};
