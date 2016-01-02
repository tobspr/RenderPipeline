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
target.set_size(1024, 1024)
target.add_color_texture(bits=8)
target.prepare_offscreen_buffer()
target.set_shader(grain_shader)

base.graphicsEngine.render_frame()

base.graphicsEngine.extract_texture_data(target["color"], base.win.get_gsg())
target["color"].write("grain.png")
