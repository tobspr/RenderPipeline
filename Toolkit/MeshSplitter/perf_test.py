"""

RenderPipeline

Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
 	 	    	 	
"""


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


for x in xrange(1):
    for y in xrange(1):
        model = loader.loadModel("Scene.bam")
        model.flatten_strong()
        model.reparent_to(render)
        model.set_scale(0.2)
        model.set_pos(x * 0.5, y * 0.5, 0)

vtx = """
#version 150

in vec4 p3d_Vertex;
in vec4 p3d_Normal;

out vec3 nrm;
uniform mat4 p3d_ModelViewProjectionMatrix;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    nrm = p3d_Normal.xyz;
}
"""

frag = """
#version 150

in vec3 nrm;
out vec4 result;

void main() {
    result = vec4(nrm, 1.0);
}

"""


base.camLens.setNearFar(0.01, 1000.0)
base.camLens.setFov(120)


shad = Shader.make(Shader.SL_GLSL, vtx, frag)

render.set_shader(shad)

base.run()
