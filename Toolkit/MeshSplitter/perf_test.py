

from panda3d.core import *

load_prc_file("../../Config/configuration.prc")
load_prc_file_data("", "show-frame-rate-meter #t")
load_prc_file_data("", "gl-debug #t")
load_prc_file_data("", "model-cache-dir ")

import direct.directbase.DirectStart

import sys
sys.path.insert(0, "../../")


from Code.Util.MovementController import MovementController


controller = MovementController(base)
controller.set_initial_position(Vec3(5), Vec3(0))
controller.setup()


for x in xrange(11):
    for y in xrange(11):
        model = loader.loadModel("Scene.bam")
        model.reparent_to(render)
        model.set_scale(0.2)
        model.set_pos(x, y, 0)

vtx = """
#version 150

in vec4 p3d_Vertex;
uniform mat4 p3d_ModelViewProjectionMatrix;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
}
"""

frag = """
#version 150

out vec4 result;

void main() {
    result = vec4(0.2, 0.6, 1.0, 1.0);
}

"""

shad = Shader.make(Shader.SL_GLSL, vtx, frag)

render.set_shader(shad)

base.run()
