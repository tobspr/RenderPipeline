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


#pragma once

#include "pandabase.h"
#include "pandaNode.h"
#include "renderState.h"
#include "shader.h"
#include "callbackData.h"

class StaticGeometryHandler;



// This node is attached to the scene graph and called last, it renders all
// static geometry to a buffer
class SGRenderNode : public PandaNode {

    PUBLISHED:
        SGRenderNode(StaticGeometryHandler* handler, PT(Shader) collector_shader);
        ~SGRenderNode();

    public:

        virtual void add_for_draw(CullTraverser *trav, CullTraverserData &data);
        virtual bool is_renderable() const;

        void do_draw_callback(CallbackData* cbdata, int reason);
        
    private:

        void create_default_geom();

        StaticGeometryHandler* _handler;
        PT(Geom) _geom_strip;
        CPT(RenderState) _base_render_state;
        CPT(RenderState) _collect_render_state;

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
