
from panda3d.core import Texture, Vec4, GeomEnums

from .DebugObject import DebugObject
from ..Globals import Globals
from ..GUI.BufferViewer import BufferViewer


class Image(DebugObject):

    """ This is a wrapper arround the Texture class from Panda3D, which keeps
    track of all images """

    @classmethod
    def create_buffer(cls, name, size, cformat, ctype):
        img = cls("Image2D-" + name)
        img.get_texture().setup_buffer_texture(size, cformat, ctype,
                                               GeomEnums.UH_static)
        img.register()
        return img

    @classmethod
    def create_2d(cls, name, w, h, cformat, ctype):
        img = cls("Image2D-" + name)
        img.get_texture().setup_2d_texture(w, h, cformat, ctype)
        img.register()
        return img

    @classmethod
    def create_2d_array(cls, name, w, h, z, cformat, ctype):
        img = cls("Image2D-" + name)
        img.get_texture().setup_2d_texture_array(w, h, z, cformat, ctype)
        img.register()
        return img

    @classmethod
    def create_3d(cls, name, w, h, z, cformat, ctype):
        img = cls("Image3D-" + name)
        img.get_texture().setup_3d_texture(w, h, z, cformat, ctype)
        img.register()
        return img

    def __init__(self, name):
        """ Internal method to create a new image """
        DebugObject.__init__(self, name)
        self._tex = Texture(name)

    def destroy(self):
        """ Destroys the image """
        raise NotImplementedError()

    def write(self, pth):
        """ Writes the image to disk """
        Globals.base.graphicsEngine.extract_texture_data(self._tex,
                                                         Globals.base.win.get_gsg())
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
