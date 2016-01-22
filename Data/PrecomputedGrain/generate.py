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
"""
Precomputes the noise for the film grain to improve performance
"""

import os
curr_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(curr_dir)

import sys
sys.path.insert(0, "../../")

from panda3d.core import *
loadPrcFile("../../Config/configuration.prc")
loadPrcFileData("", "textures-power-2 none")
loadPrcFileData("", "window-type offscreen")
loadPrcFileData("", "win-size 100 100")

grain_shader = Shader.load(
  Shader.SL_GLSL,
  "../../Shader/DefaultPostProcess.vert.glsl",
  "GrainShader.fragment.glsl")

import direct.directbase.DirectStart

from Code.RenderTarget import RenderTarget

target = RenderTarget()
target.size = 1024, 1024
target.add_color_texture(bits=8)
target.prepare_offscreen_buffer()
target.set_shader(grain_shader)

base.graphicsEngine.render_frame()

base.graphicsEngine.extract_texture_data(target["color"], base.win.get_gsg())
target["color"].write("grain.png")
