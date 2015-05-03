
from panda3d.core import TransparencyAttrib, Vec3, Texture
from direct.gui.OnscreenImage import OnscreenImage

from ..DebugObject import DebugObject


class BetterOnscreenImage(DebugObject):

    """ Simple wrapper arroun OnscreenImage, providing a simpler interface and
    better visuals """

    def __init__(self, image=None, parent=None, x=0, y=0, w=10, h=10,
                 transparent=True, nearFilter=True, anyFilter=True):
        """ Creates a new image, taking (x,y) as topleft coordinates.

        When nearFilter is set to true, a near filter will be set to the
        texture passed. This provides sharper images.

        When anyFilter is set to false, the passed image won't be modified at
        all. This enables you to display existing textures, otherwise the
        texture would get a near filter in the 3D View, too. """

        DebugObject.__init__(self, "BetterOnscreenImage")

        self.w, self.h = w, h
        self.initialPos = self.translatePos(x, y)

        self._node = OnscreenImage(
            image=image, parent=parent, pos=self.initialPos,
            scale=(w / 2.0, 1, h / 2.0))

        if transparent:
            self._node.setTransparency(TransparencyAttrib.MAlpha)

        tex = self._node.getTexture()

        if nearFilter and anyFilter:
            tex.setMinfilter(Texture.FTNearest)
            tex.setMagfilter(Texture.FTNearest)

        if anyFilter:
            tex.setAnisotropicDegree(8)
            tex.setWrapU(Texture.WMClamp)
            tex.setWrapV(Texture.WMClamp)

    def getInitialPos(self):
        """ Returns the initial position of the image. This can be used for
        animations """
        return self.initialPos

    def posInterval(self, *args, **kwargs):
        """ Returns a pos interval, this is a wrapper arround
        NodePath.posInterval """
        return self._node.posInterval(*args, **kwargs)

    def hprInterval(self, *args, **kwargs):
        """ Returns a hpr interval, this is a wrapper arround
        NodePath.hprInterval """
        return self._node.hprInterval(*args, **kwargs)

    def setImage(self, img):
        """ Sets the current image """
        self._node.setImage(img)

    def setPos(self, x, y):
        """ Sets the position """
        self.initialPos = self.translatePos(x, y)
        self._node.setPos(self.initialPos)

    def translatePos(self, x, y):
        """ Converts 2d coordinates to pandas coordinate system """
        return Vec3(x + self.w / 2.0, 1, -y - self.h / 2.0)


    def hide(self):
        self._node.hide()

    def show(self):
        self._node.show()
