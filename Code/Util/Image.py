
from panda3d.core import Texture, Vec4, GeomEnums

from DebugObject import DebugObject
from FunctionDecorators import protected
from ..Globals import Globals

from ..GUI.BufferViewer import BufferViewer

class Image(DebugObject):

    """ This is a wrapper arround the Texture class from Panda3D, which keeps
    track of all images """

    @classmethod
    def createBuffer(self, name, size, cformat, ctype):
        img = self("Image2D-" + name)
        img.tex = Texture(name)
        img.tex.setupBufferTexture(size, cformat, ctype, GeomEnums.UHStatic)
        img.register()
        return img

    @classmethod
    def create2D(self, name, w, h, cformat, ctype):
        img = self("Image2D-" + name)
        img.tex = Texture(name)
        img.tex.setup2dTexture( w, h, cformat, ctype)
        img.register()
        return img

    @classmethod
    def create2DArray(self, name, w, h, z, cformat, ctype):
        img = self("Image2D-" + name)
        img.tex = Texture(name)
        img.tex.setup2dTextureArray( w, h, z, cformat, ctype)
        img.register()
        return img

    @classmethod
    def create3D(self, name, w, h, z, cformat, ctype):
        img = self("Image3D-" + name)
        img.tex = Texture(name)
        img.tex.setup3dTexture( w, h, z, cformat, ctype)
        img.register()
        return img

    @protected
    def __init__(self, name):
        """ Internal method """ 
        DebugObject.__init__(self, name)
        # self.debug("Constructed new image '" + name + "'")
        self.tex = None

    def destroy(self):
        """ Destroys the image """
        raise NotImplementedError()

    def write(self, pth):
        """ Writes the image to disk """
        Globals.base.graphicsEngine.extractTextureData(self.tex, Globals.base.win.getGsg())
        self.tex.write(pth)

    def register(self):
        """ Registers the image for memory tracking and debugging """
        BufferViewer.registerEntry(self)

    def setClearColor(self, *args):
        """ Sets the clear color of the texture """
        self.tex.setClearColor(Vec4(*args))

    def clearImage(self):
        """ Clears the texture to the color specified with setClearColor """
        self.tex.clearImage()