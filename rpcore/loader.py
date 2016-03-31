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

from __future__ import print_function

import time

from panda3d.core import PNMImage, VirtualFileSystem, VirtualFileMountRamdisk
from panda3d.core import Shader

from rpcore.globals import Globals
from rpcore.rpobject import RPObject

class sync_loading_op(object):
    def __init__(self, resource):
        self.resource = resource
        if isinstance(self.resource, (list, tuple)):
            self.resource = ', '.join(self.resource)

    def __enter__(self):
        self.start_time = time.clock()

    def __exit__(self, *args):
        duration = (time.clock() - self.start_time) * 1000.0
        if duration > 70.0:
            print("WARNING: Loading '" + self.resource + "' took", round(duration, 2), "ms")

class RPLoader(RPObject):

    @classmethod
    def load_texture(cls, filename):
        with sync_loading_op(filename):
            return Globals.base.loader.load_texture(filename)

    @classmethod
    def load_cube_map(cls, filename, read_mipmaps=False):
        with sync_loading_op(filename):
            return Globals.base.loader.load_cube_map(filename, readMipmaps=read_mipmaps)

    @classmethod
    def load_3d_texture(cls, filename):
        with sync_loading_op(filename):
            return Globals.base.loader.load_3d_texture(filename)

    @classmethod
    def load_font(cls, filename):
        with sync_loading_op(filename):
            return Globals.base.loader.load_font(filename)

    @classmethod
    def load_shader(cls, *args):
        with sync_loading_op(args):
            if len(args) == 1:
                return Shader.load_compute(Shader.SL_GLSL, args[0])
            return Shader.load(Shader.SL_GLSL, *args)

    @classmethod
    def load_model(cls, filename):
        with sync_loading_op(filename):
            return Globals.base.loader.load_model(filename)

    @classmethod
    def load_sliced_3d_texture(cls, fname, tile_size_x, tile_size_y=None, num_tiles=None):
        """ Loads a texture from the given filename and dimensions. If only
        one dimensions is specified, the other dimensions are assumed to be
        equal. This internally loads the texture into ram, splits it into smaller
        sub-images, and then calls the load_3d_texture from the Panda loader """

        tempfile_name = "/$$slice_loader_temp-" + str(time.time()) + "/"
        tile_size_y = tile_size_x if tile_size_y is None else tile_size_y
        num_tiles = tile_size_x if num_tiles is None else num_tiles

        # Load sliced image from disk
        source = PNMImage(fname)
        width = source.get_x_size()

        # Find slice properties
        num_cols = width // tile_size_x
        temp = PNMImage(
            tile_size_x, tile_size_y, source.get_num_channels(), source.get_maxval())

        # Construct a ramdisk to write the files to
        vfs = VirtualFileSystem.get_global_ptr()
        ramdisk = VirtualFileMountRamdisk()
        vfs.mount(ramdisk, tempfile_name, 0)

        # Extract all slices and write them to the virtual disk
        for z_slice in range(num_tiles):
            slice_x = (z_slice % num_cols) * tile_size_x
            slice_y = (z_slice // num_cols) * tile_size_y
            temp.copy_sub_image(source, 0, 0, slice_x, slice_y, tile_size_x, tile_size_y)
            temp.write(tempfile_name + str(z_slice) + ".png")

        # Load the de-sliced texture from the ramdisk
        texture_handle = RPLoader.load_3d_texture(tempfile_name + "/#.png")
        vfs.unmount(ramdisk)

        return texture_handle
