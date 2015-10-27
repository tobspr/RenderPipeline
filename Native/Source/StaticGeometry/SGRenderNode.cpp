

#include "SGRenderNode.h"

#include "dtool_config.h"

#include "omniBoundingVolume.h"
#include "cullBinAttrib.h"
#include "cullableObject.h"
#include "geomVertexFormat.h"
#include "cullHandler.h"
#include "geomVertexWriter.h"
#include "geomTriangles.h"
#include "shaderAttrib.h"
#include "geomVertexData.h"
#include "geom.h"


#include "StaticGeometryHandler.h"
#include "SGRenderCallback.h"

#include "glgsg.h"


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
    sattrib = DCAST(ShaderAttrib, sattrib)->set_shader_input("DrawnObjectsTex", handler->get_drawn_objects_tex());
    sattrib = DCAST(ShaderAttrib, sattrib)->set_shader_input("DynamicStripsTex", handler->get_dynamic_strips_tex());

    _base_render_state = RenderState::make(sattrib);

    CPT(RenderAttrib) collect_attrib = sattrib;
    collect_attrib = DCAST(ShaderAttrib, collect_attrib)->set_shader(collector_shader, 100000);
    collect_attrib = DCAST(ShaderAttrib, collect_attrib)->set_shader_input("IndirectTex", handler->get_indirect_tex());
  
    _collect_render_state = RenderState::make(collect_attrib);

}

SGRenderNode::~SGRenderNode() {

}


bool SGRenderNode::is_renderable() const {
  return true;
}

void SGRenderNode::add_for_draw(CullTraverser *trav, CullTraverserData &data) {


    // Execute the collector shader
    CullableObject *collect_obj = new CullableObject(NULL, 
        data._state->compose(_collect_render_state), TransformState::make_identity());
    collect_obj->set_draw_callback(new SGRenderCallback(this, 0));
    trav->get_cull_handler()->record_object(collect_obj, trav);


    // Finally render the triangle strip
    CPT(TransformState) internal_transform = data.get_internal_transform(trav);
    CPT(RenderState) state = _base_render_state->compose(data._state);
    CullableObject *object = 
      new CullableObject(_geom_strip, state, internal_transform);
    object->set_draw_callback(new SGRenderCallback(this, 1));
    trav->get_cull_handler()->record_object(object, trav);

    _handler->clear_render_list();

}

void SGRenderNode::do_draw_callback(CallbackData* cbdata, int reason) {

    GeomDrawCallbackData *data = (GeomDrawCallbackData *)cbdata;
    CullableObject *obj = data->get_object();
    GraphicsStateGuardianBase *gsg = data->get_gsg();
	
    if (reason == 0) {
        // Execute collector shader
        gsg->dispatch_compute(1, 1, 1);
    } else if (reason == 1) {
        // Render default object
			
		Thread *current_thread = Thread::get_current_thread();
		
		const GeomPipelineReader geom_reader(obj->_geom, current_thread);

		CPT(GeomVertexData) vertex_data = geom_reader.get_vertex_data();
		PT(GeomMunger) munger = gsg->get_geom_munger(obj->_state, current_thread);
		if (!munger->munge_geom(obj->_geom, vertex_data, true, current_thread)) {
			cout << "ERROR: munge geom failed " << endl;
			return;
		}

		const GeomVertexDataPipelineReader data_reader(vertex_data, current_thread);
		data_reader.check_array_readers();

		if (!gsg->begin_draw_primitives(&geom_reader, munger, &data_reader, true)) {
			cout << "Error: begin draw primitives failed" << endl;
			return;
		}

		// Prepare the image buffer texture
		TextureContext* tc = _handler->get_indirect_tex()->prepare_now( 0, gsg->get_prepared_objects(), gsg );
		GLTextureContext *gtc = (GLTextureContext*)tc;
		gsg->update_texture(gtc, true);
		assert(gtc->_buffer != 0);

		GLGraphicsStateGuardian* glgsg = (GLGraphicsStateGuardian*)gsg;

		glgsg->_glBindBuffer(GL_DRAW_INDIRECT_BUFFER, gtc->_buffer);
		glgsg->_glMultiDrawArraysIndirect(GL_TRIANGLES, 0, 1, 0);

		gsg->end_draw_primitives();


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


