



from panda3d.core import *
from random import random


load_prc_file("../../Config/configuration.prc")
load_prc_file_data("", "show-frame-rate-meter #t")
load_prc_file_data("", "gl-debug #f")
# load_prc_file_data("", "notify-level-glgsg debug")

import direct.directbase.DirectStart

import sys
sys.path.insert(0, "../../")

from Native.RSNative import StaticGeometryHandler, SGNode, SGRenderNode
from Code.Util.MovementController import MovementController


controller = MovementController(base)
controller.set_initial_position(Vec3(5), Vec3(0))
controller.setup()


vtx_shader = """
#version 150


uniform mat4 p3d_ModelViewProjectionMatrix;

in vec4 p3d_Vertex;

uniform sampler2D DatasetTex;
uniform isamplerBuffer DynamicStripsTex;

uniform samplerBuffer DrawnObjectsTex;

out vec4 col;

void main() {
    
    int strip_offs = gl_InstanceID;
    int vtx_idx = gl_VertexID;

    int object_id = texelFetch(DynamicStripsTex, strip_offs * 2 + 1).x;
    int strip_id = texelFetch(DynamicStripsTex, strip_offs * 2 + 2).x;



    // Read transform from object data
    int dobj_offs = 1 + 5 * object_id;

    vec4 mt0 = texelFetch(DrawnObjectsTex, dobj_offs + 1).rgba;
    vec4 mt1 = texelFetch(DrawnObjectsTex, dobj_offs + 2).rgba;
    vec4 mt2 = texelFetch(DrawnObjectsTex, dobj_offs + 3).rgba;
    vec4 mt3 = texelFetch(DrawnObjectsTex, dobj_offs + 4).rgba;

    mat4 transform = mat4(mt0, mt1, mt2, mt3); 

    int data_offs = 2 + vtx_idx;

    vec4 data0 = texelFetch(DatasetTex, ivec2(data_offs + 0, strip_id), 0).bgra;
    //vec4 data1 = texelFetch(DatasetTex, ivec2(data_offs + 1, strip_offs), 0).abgr;

    vec4 vtx_pos = vec4(data0.xyz, 1);

    col = vec4(strip_id / 200.0, 1.0 - (strip_id / 200.0), 0, 1);
    col.w = 1.0;

    vec3 nrm = normalize(vtx_pos.xyz);

    vtx_pos = transform * vtx_pos;

    col.xyz = nrm;

    gl_Position = p3d_ModelViewProjectionMatrix * vtx_pos;    
} """


frag_shader = """
#version 150

in vec4 col;
out vec4 result;

void main() {

    result = col;
}
"""

shader = Shader.make(Shader.SL_GLSL, vtx_shader, frag_shader)


# This is usually done by the pipeline
handler = StaticGeometryHandler()


# Load model
model_dataset = handler.load_dataset("model.rpsg")

for x in xrange(11):
    for y in xrange(11):

        node = SGNode("test", handler, model_dataset)
        np = render.attach_new_node(node)

        np.set_scale(0.2)
        np.set_pos(x*0.5, y*0.5, 0)



# np.set_scale(0.5)
collect_shader = Shader.load_compute(Shader.SL_GLSL, "collect_objects.compute.glsl")


finish_node = SGRenderNode(handler, collect_shader)
finish_np = render.attach_new_node(finish_node)
finish_np.set_shader(shader, 1000)
base.run()

sys.exit(0)





