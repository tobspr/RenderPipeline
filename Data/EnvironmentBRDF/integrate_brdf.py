
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