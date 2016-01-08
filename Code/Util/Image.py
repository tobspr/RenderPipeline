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

from panda3d.core import Texture, Vec4, GeomEnums

from .DebugObject import DebugObject
from ..Globals import Globals
from ..GUI.BufferViewer import BufferViewer


class Image(DebugObject):

    """ This is a wrapper arround the Texture class from Panda3D, which keeps
    track of all images """

    # Total amount of images
    _NUM_IMAGES = 0

    @classmethod
    def create_buffer(cls, name, size, comp_type, comp_format):
        img = cls("ImageBuffer-" + name)
        img.get_texture().setup_buffer_texture(size, comp_type, comp_format,
                                               GeomEnums.UH_static)
        img.register()
        return img

    @classmethod
    def create_2d(cls, name, w, h, comp_type, comp_format):
        img = cls("Image2D-" + name)
        img.get_texture().setup_2d_texture(w, h, comp_type, comp_format)
        img.register()
        return img

    @classmethod
    def create_2d_array(cls, name, w, h, slices, comp_type, comp_format):
        img = cls("Image2DArr-" + name)
        img.get_texture().setup_2d_texture_array(w, h, slices, comp_type, comp_format)
        img.register()
        return img

    @classmethod
    def create_3d(cls, name, w, h, slices, comp_type, comp_format):
        img = cls("Image3D-" + name)
        img.get_texture().setup_3d_texture(w, h, slices, comp_type, comp_format)
        img.register()
        return img

    @classmethod
    def create_cube(cls, name, size, comp_type, comp_format):
        img = cls("ImageCube-" + name)
        img.get_texture().setup_cube_map(size, comp_type, comp_format)
        img.register()
        return img

    def __init__(self, name):
        """ Internal method to create a new image """
        DebugObject.__init__(self, name)
        Image._NUM_IMAGES += 1
        self._tex = Texture(name)

    def destroy(self):
        """ Destroys the image """
        raise NotImplementedError()

    def write(self, pth):
        """ Writes the image to disk """
        Globals.base.graphicsEngine.extract_texture_data(self._tex,
                                                         Globals.base.win.get_gsg())
        if self._tex.get_texture_type() == Texture.TT_3d_texture:
            self._tex.write(pth, 0, 0, True, False)
        else:
            self._tex.write(pth)

    def register(self):
        """ Registers the image for memory tracking and debugging """
        BufferViewer.register_entry(self)

    def set_clear_color(self, *args):
        """ Sets the clear color of the texture """
        self._tex.set_clear_color(Vec4(*args))

    def clear_image(self):
        """ Clears the texture to the color specified with setClearColor """
        self._tex.clear_image()

    def get_texture(self):
        """ Returns a handle to the texture """
        return self._tex
