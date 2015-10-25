



from panda3d.core import *
from random import random
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
uniform isampler2D MappingTex;

out vec4 col;

void main() {

    int strip_idx = gl_InstanceID;
    int vtx_idx = gl_VertexID;

    int obj_idx = 0;
    int strip_offs = texelFetch(MappingTex, ivec2(strip_idx, obj_idx), 0).x;


    int data_offs = vtx_idx * 2;

    vec4 data0 = texelFetch(DatasetTex, ivec2(data_offs + 0, strip_offs), 0).bgra;
    vec4 data1 = texelFetch(DatasetTex, ivec2(data_offs + 1, strip_offs), 0).abgr;

    vec4 vtx_pos = vec4(data0.xyz, 1);

    col = vec4(vtx_idx / 256.0);
    col.w = 1.0;
    col.r = 0.0;

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
node = SGNode("test", handler, model_dataset)
np = render.attach_new_node(node)


# render.set_pos(10, 10, 5)


# np.set_scale(0.5)

finish_node = SGRenderNode(handler)
finish_np = render.attach_new_node(finish_node)
finish_np.set_shader(shader, 1000)
finish_np.set_instance_count(23)
finish_np.set_two_sided(True)
base.run()

sys.exit(0)





