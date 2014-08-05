
from panda3d.core import TransparencyAttrib, Vec3, Texture
from DebugObject import DebugObject
from direct.gui.OnscreenImage import OnscreenImage


class BetterOnscreenImage(DebugObject):

    def __init__(self, image=None, parent=None, x=0, y=0, w=10, h=10, transparent=True, nearFilter=True):
        DebugObject.__init__(self, "BOnscreenImage")

        self.initialPos = Vec3(x + w / 2.0, 1, -y - h / 2.0)

        self._node = OnscreenImage(
            image=image, parent=parent, pos=self.initialPos, scale=(w / 2.0,  1, h / 2.0))

        if transparent:
            self._node.setTransparency(TransparencyAttrib.MAlpha)

        tex = self._node.getTexture()
        tex.setMinfilter(Texture.FTNearest)
        tex.setMagfilter(Texture.FTNearest)
        tex.setAnisotropicDegree(8)
        tex.setWrapU(Texture.WMClamp)
        tex.setWrapV(Texture.WMClamp)

    def getInitialPos(self):
        return self.initialPos

    def posInterval(self, *args, **kwargs):
        return self._node.posInterval(*args, **kwargs)
