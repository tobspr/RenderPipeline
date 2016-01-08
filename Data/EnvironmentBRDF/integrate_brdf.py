"""

RenderPipeline

Copyright (c) 2014-2015 tobspr <tobias.springer1@gmail.com>

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

""" This file pre-integrates the environment BRDF.

SOURCE:
"Real Shading in Unreal Engine 4"
https://de45xmedrsdbp.cloudfront.net/Resources/files/2013SiggraphPresentationsNotes-26915738.pdf
"""

from __future__ import division, print_function

from panda3d.core import *

load_prc_file_data("", """
textures-power-2 none
win-size 100 100
""")

import direct.directbase.DirectStart

res = 256

dest = Texture("")
dest.setup_2d_texture(res, res, Texture.T_float, Texture.F_rgba16)




# Create a dummy node and apply the shader to it
shader = Shader.load_compute(Shader.SL_GLSL, "filtering.compute.glsl")
dummy = NodePath("dummy")
dummy.set_shader(shader)
dummy.set_shader_input("Dest", dest)
sattr = dummy.get_attrib(ShaderAttrib)
base.graphicsEngine.dispatch_compute(( (res + 15) // 16, (res + 15) // 16, 1), sattr, base.win.get_gsg())

base.graphicsEngine.extract_texture_data(dest, base.win.get_gsg())
dest.write("PrefilteredEnvBRDF.png")

print("Done!")