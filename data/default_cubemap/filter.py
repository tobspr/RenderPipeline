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

# pylint: skip-file

from __future__ import print_function, division

import os
import sys
import random
import shutil
from os.path import dirname, realpath, join

from panda3d.core import *
from direct.stdpy.file import isdir, isfile, join
from direct.showbase.ShowBase import ShowBase

BASE_PATH = realpath(dirname(__file__))
sys.path.insert(0, join(BASE_PATH, "..", ".."))

from rplibs.progressbar import FileTransferSpeed, ETA, ProgressBar, Percentage
from rplibs.progressbar import Bar

class Application(ShowBase):
    def __init__(self):
        load_prc_file_data("", """
            textures-power-2 none
            window-type offscreen
            win-size 100 100
            gl-coordinate-system default
            notify-level-display error
            print-pipe-types #f
            gl-finish #t
            gl-debug #t
        """)

        print("init showbase")
        ShowBase.__init__(self)
        print("done..")

        os.chdir(BASE_PATH)

        source_path = join(BASE_PATH, "source")
        extension = ".jpg"
        if isfile(join(source_path, "1.png")):
            extension = ".png"

        # Initial update
        self.taskMgr.step()

        print("Loading source data ..")
        cubemap = self.loader.load_texture("source/envmap.hdr")

        print("Filtering diffuse cubemap ..")
        diffuse_size = 16

        cshader = Shader.load_compute(Shader.SL_GLSL, "filter_diffuse.compute.glsl")

        dest_cubemap = Texture("Dest")
        dest_cubemap.setup_cube_map(diffuse_size, Texture.T_float, Texture.F_rgba16)
        dest_cubemap.set_minfilter(Texture.FT_linear)
        dest_cubemap.set_magfilter(Texture.FT_linear)
        dest_cubemap.set_clear_color(Vec4(0))
        dest_cubemap.clear_image()

        for i in range(6):
            node = NodePath("")
            node.set_shader_input("SourceTex", cubemap)
            node.set_shader_input("DestTex", dest_cubemap, False, True, -1, 0, i)
            node.set_shader_input("totalSize", diffuse_size)
            node.set_shader_input("currentFace", i)
            node.set_shader(cshader)
            attr = node.get_attrib(ShaderAttrib)
            self.graphicsEngine.dispatch_compute(((diffuse_size + 15) // 16, (diffuse_size + 15) // 16, 1), attr, self.win.gsg)

        self.graphicsEngine.extract_texture_data(dest_cubemap, self.win.gsg)
        dest_cubemap.write("cubemap_diffuse.txo")

        print("Generating specular workload ..")
        mipmap, size = -1, 1024
        cshader = Shader.load_compute(Shader.SL_GLSL, "filter_specular.compute.glsl")

        dest_cubemap = Texture("Dest")
        dest_cubemap.setup_cube_map(size, Texture.T_float, Texture.F_rgba16)
        dest_cubemap.set_minfilter(Texture.FT_linear_mipmap_linear)
        dest_cubemap.set_magfilter(Texture.FT_linear)
        dest_cubemap.set_clear_color(Vec4(0))
        dest_cubemap.clear_image()

        random.seed(123)

        workload = []

        while size >= 1:
            mipmap += 1
            passes = 32 + max(0, mipmap - 1) * 48
            passes = 10
            node = NodePath("")

            for i in range(6):
                node.set_shader(cshader)
                node.set_shader_input("SourceTex", cubemap)
                node.set_shader_input("DestTex", dest_cubemap, False, True, -1, mipmap, i)
                node.set_shader_input("currentSize", size)
                node.set_shader_input("currentMip", mipmap)
                node.set_shader_input("currentFace", i)
                node.set_shader_input("weight", 1.0 / passes)
                for n in range(passes):
                    node.set_shader_input("seed", random.random())
                    attr = node.get_attrib(ShaderAttrib)
                    workload.append((((size + 15) // 16, (size+15) // 16, 1), attr))

            size = size // 2

        widgets = ['Filtering: ', Bar(), Percentage(), '   ', ETA()]
        progressbar = ProgressBar(widgets=widgets, maxval=len(workload) - 1).start()
        for i, (wg_size, attr) in enumerate(workload):
            self.graphicsEngine.dispatch_compute(wg_size, attr, self.win.gsg)
            progressbar.update(i)
        progressbar.finish()

        print("Writing txo ..")

        self.graphicsEngine.extract_texture_data(dest_cubemap, self.win.gsg)
        dest_cubemap.write("cubemap_specular.txo")

        print("Done.")

Application()
