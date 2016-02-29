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

from __future__ import print_function, division

import os
import shutil
from os.path import dirname, realpath
from direct.stdpy.file import isdir, isfile, join
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase



class Application(ShowBase):
    def __init__(self):
        load_prc_file_data("", """
            textures-power-2 none
            window-type offscreen
            win-size 100 100
            gl-coordinate-system default
            notify-level-display error
            print-pipe-types #f
        """)

        ShowBase.__init__(self)

        base_path = realpath(dirname(__file__))
        os.chdir(base_path)
        slice_dir = join(base_path, "slices/")
        if isdir(slice_dir):
            shutil.rmtree(slice_dir)
        os.makedirs(slice_dir)

        node = NodePath("")

        w, h, d = 512, 512, 64

        self.voxel_grid = Texture("voxels")
        self.voxel_grid.setup_3d_texture(w, h, d, Texture.T_unsigned_byte, Texture.F_rgba8)


        # Generate grid
        cshader = Shader.load_compute(Shader.SL_GLSL, "generate_grid.compute.glsl")
        node.set_shader(cshader)
        node.set_shader_input("DestTex", self.voxel_grid)
        attr = node.get_attrib(ShaderAttrib)

        self.graphicsEngine.dispatch_compute(
            ((w + 7) // 8, (h + 7) // 8, (d + 3) // 4), attr, self.win.get_gsg())

        self.graphicsEngine.extract_texture_data(self.voxel_grid, self.win.get_gsg())

        print("Writing data ..")
        self.voxel_grid.write(Filename.from_os_specific(join(slice_dir, "#.png")), 0, 0, True, False)

Application()
