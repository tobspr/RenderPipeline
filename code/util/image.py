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

from panda3d.core import Texture, Vec4, GeomEnums

from ..rp_object import RPObject
from ..globals import Globals
from ..gui.buffer_viewer import BufferViewer

class Image(RPObject, Texture):

    """ This is a wrapper arround the Texture class from Panda3D, which keeps
    track of all images and registers / unregisters them aswell as counting
    the memory used. """

    # Total amount of images
    _NUM_IMAGES = 0

    @classmethod
    def create_buffer(cls, name, size, comp_type, comp_format):
        """ Creates a new buffer texture """
        img = cls("ImgBuffer-" + name)
        img.setup_buffer_texture(size, comp_type, comp_format, GeomEnums.UH_static)
        return img

    @classmethod
    def create_2d(cls, name, w, h, comp_type, comp_format):
        """ Creates a new 2D texture """
        img = cls("Img2D-" + name)
        img.setup_2d_texture(w, h, comp_type, comp_format)
        return img

    @classmethod
    def create_2d_array(cls, name, w, h, slices, comp_type, comp_format):
        """ Creates a new 2D-array texture """
        img = cls("Img2DArr-" + name)
        img.setup_2d_texture_array(w, h, slices, comp_type, comp_format)
        return img

    @classmethod
    def create_3d(cls, name, w, h, slices, comp_type, comp_format):
        """ Creates a new 3D texture """
        img = cls("Img3D-" + name)
        img.setup_3d_texture(w, h, slices, comp_type, comp_format)
        return img

    @classmethod
    def create_cube(cls, name, size, comp_type, comp_format):
        """ Creates a new cubemap """
        img = cls("ImgCube-" + name)
        img.setup_cube_map(size, comp_type, comp_format)
        return img

    def __init__(self, name):
        """ Internal method to create a new image """
        RPObject.__init__(self, name)
        Texture.__init__(self, name)
        Image._NUM_IMAGES += 1
        BufferViewer.register_entry(self)

    def __del__(self):
        """ Destroys the image """
        self.warn("Image destructor not implemented yet")

    def write(self, pth):
        """ Writes the image to disk """
        Globals.base.graphicsEngine.extract_texture_data(self._tex,
                                                         Globals.base.win.get_gsg())
        if self.get_texture_type() == Texture.TT_3d_texture:
            Texture.write(self, pth, 0, 0, True, False)
        else:
            Texture.write(self, pth)
