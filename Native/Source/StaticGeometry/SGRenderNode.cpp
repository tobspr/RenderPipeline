

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

#include "../common.h"

SGRenderNode::SGRenderNode(StaticGeometryHandler *handler) : PandaNode("SGRender") {
    _handler = handler;
    set_internal_bounds(new OmniBoundingVolume);
    set_final(true);
    create_default_geom();


    CPT(RenderAttrib) sattrib = ShaderAttrib::make_off();
    sattrib = DCAST(ShaderAttrib, sattrib)->set_shader_input("DatasetTex", handler->get_dataset_tex());
    sattrib = DCAST(ShaderAttrib, sattrib)->set_shader_input("MappingTex", handler->get_mapping_tex());
    sattrib = DCAST(ShaderAttrib, sattrib)->set_instance_count(153);

    _base_render_state = RenderState::make(
        sattrib
    );
}


SGRenderNode::~SGRenderNode() {


}



bool SGRenderNode::is_renderable() const {
  return true;
}

void SGRenderNode::add_for_draw(CullTraverser *trav, CullTraverserData &data) {

    CPT(TransformState) internal_transform = data.get_internal_transform(trav);

    // Combine state
    CPT(RenderState) state = _base_render_state->compose(data._state);


    CullableObject *object =
      new CullableObject(_geom_strip, state, internal_transform);
    trav->get_cull_handler()->record_object(object, trav);

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