
from panda3d.core import Texture, Vec4, GeomEnums

from DebugObject import DebugObject
from ..Globals import Globals
from ..GUI.BufferViewer import BufferViewer


class Image(DebugObject):

    """ This is a wrapper arround the Texture class from Panda3D, which keeps
    track of all images """

    @classmethod
    def create_buffer(cls, name, size, cformat, ctype):
        img = cls("Image2D-" + name)
        img.tex = Texture(name)
        img.tex.setup_buffer_texture(size, cformat, ctype, GeomEnums.UHStatic)
        img.register()
        return img

    @classmethod
    def create_2d(cls, name, w, h, cformat, ctype):
        img = cls("Image2D-" + name)
        img.tex = Texture(name)
        img.tex.setup_2d_texture(w, h, cformat, ctype)
        img.register()
        return img

    @classmethod
    def create_2d_array(cls, name, w, h, z, cformat, ctype):
        img = cls("Image2D-" + name)
        img.tex = Texture(name)
        img.tex.setup_2d_texture_array(w, h, z, cformat, ctype)
        img.register()
        return img

    @classmethod
    def create_3d(cls, name, w, h, z, cformat, ctype):
        img = cls("Image3D-" + name)
        img.tex = Texture(name)
        img.tex.setup_3d_texture(w, h, z, cformat, ctype)
        img.register()
        return img

    def __init__(self, name):
        """ Internal method to create a new image """
        DebugObject.__init__(self, name)
        self.tex = None

    def destroy(self):
        """ Destroys the image """
        raise NotImplementedError()

    def write(self, pth):
        """ Writes the image to disk """
        Globals.base.graphicsEngine.extractTextureData(self.tex,
            Globals.base.win.getGsg())
        self.tex.write(pth)

    def register(self):
        """ Registers the image for memory tracking and debugging """
        BufferViewer.registerEntry(self)

    def set_clear_color(self, *args):
        """ Sets the clear color of the texture """
        self.tex.set_clear_color(Vec4(*args))

    def clear_image(self):
        """ Clears the texture to the color specified with setClearColor """
        self.tex.clear_image()
