

#include "SGRenderNode.h"

#include "omniBoundingVolume.h"
#include "cullBinAttrib.h"
#include "cullableObject.h"
#include "geomVertexFormat.h"
#include "cullHandler.h"
#include "geomVertexWriter.h"
#include "geomTriangles.h"
#include "shaderAttrib.h"
#include "geom.h"

#include "StaticGeometryHandler.h"
#include "SGRenderCallback.h"

#include "../common.h"

TypeHandle SGRenderNode::_type_handle;

SGRenderNode::SGRenderNode(StaticGeometryHandler *handler, PT(Shader) collector_shader) : PandaNode("SGRender") {
    _handler = handler;
    set_internal_bounds(new OmniBoundingVolume);
    set_final(true);
    create_default_geom();


    CPT(RenderAttrib) sattrib = ShaderAttrib::make_off();
    sattrib = DCAST(ShaderAttrib, sattrib)->set_shader_input("DatasetTex", handler->get_dataset_tex());
    sattrib = DCAST(ShaderAttrib, sattrib)->set_shader_input("MappingTex", handler->get_mapping_tex());
    sattrib = DCAST(ShaderAttrib, sattrib)->set_shader_input("IndirectTex", handler->get_indirect_tex());
    sattrib = DCAST(ShaderAttrib, sattrib)->set_shader_input("DrawnObjectsTex", handler->get_drawn_objects_tex());
    sattrib = DCAST(ShaderAttrib, sattrib)->set_shader_input("DynamicStripsTex", handler->get_dynamic_strips_tex());

    _base_render_state = RenderState::make(
        sattrib
    );


    _collect_render_state = RenderState::make(
        DCAST(ShaderAttrib, sattrib)->set_shader(collector_shader)
    );

}

SGRenderNode::~SGRenderNode() {

}


bool SGRenderNode::is_renderable() const {
  return true;
}

void SGRenderNode::add_for_draw(CullTraverser *trav, CullTraverserData &data) {


    // Execute the collector shader
    CullableObject *collect_obj = new CullableObject(NULL, _collect_render_state, TransformState::make_identity());
    collect_obj->set_draw_callback(new SGRenderCallback(this, 0));
    trav->get_cull_handler()->record_object(collect_obj, trav);


    // Finally render the triangle strip
    CPT(TransformState) internal_transform = data.get_internal_transform(trav);
    CPT(RenderState) state = _base_render_state->compose(data._state);
    CullableObject *object =
      new CullableObject(_geom_strip, state, internal_transform);
    trav->get_cull_handler()->record_object(object, trav);

    _handler->clear_render_list();

}

void SGRenderNode::do_draw_callback(CallbackData* cbdata, int reason) {

    GeomDrawCallbackData *data = (GeomDrawCallbackData *)cbdata;
    GraphicsStateGuardianBase *gsg = data->get_gsg();

    // cout << "Doing draw callback with reason " << reason << endl;
    // gsg->dispatch_compute(it->get_x(), it->get_y(), it->get_z());

    if (reason == 0) {
        // Execute collector shader
        gsg->dispatch_compute(1, 1, 1);
    }


}


void SGRenderNode::create_default_geom() {

    CPT(GeomVertexFormat) vformat = GeomVertexFormat::get_v3();
    PT(GeomVertexData) vdata = new GeomVertexData("vdata", vformat, Geom::UH_static);
    vdata->set_num_rows(SG_TRI_GROUP_SIZE * 3);

    GeomVertexWriter writer(vdata, "vertex");

    for (size_t i = 0; i < SG_TRI_GROUP_SIZE; ++i) {
        writer.add_data3f(0, 0, 0);
        writer.add_data3f(0, 1, 0);
        writer.add_data3f(1, 1, 0);
    }

    PT(GeomTriangles) triangles = new GeomTriangles(Geom::UH_static);
    triangles->add_next_vertices(SG_TRI_GROUP_SIZE * 3);
    
    _geom_strip = new Geom(vdata);
    _geom_strip->add_primitive(triangles);
}


