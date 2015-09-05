
from panda3d.core import Vec3

from ..Util.DebugObject import DebugObject
from ..Util.FunctionDecorators import protected

class Light(DebugObject):

    """ This is the abstract base class for all Lights """

    # Light Types
    LTNone = 0
    LTPointLight = 1

    def __init__(self):
        DebugObject.__init__(self, "Light")
        self.position = Vec3(0)
        self.color = Vec3(0)

    def getLightType(self):
        """ Returns the type of the light, should be overriden by subclasses """
        raise NotImplementedError()

    def addToStream(self, command):
        """ Adds the light to a command stream, subclasses should implement this,
        and call this method, then add their own data """
        command.pushInt(self.getLightType())
        command.pushVec3(self.position)
        command.pushVec3(self.color)
        
    def setPos(self, *args):
        """ Sets the light position. Accepts the same parameters as a Vec3 """
        self.position = Vec3(*args)
        self._markDirty()

    def setColor(self, *args):
        """ Sets the light color. Accepts the same parameters as a Vec3 """
        self.color = Vec3(*args)
        self._markDirty()

    def __repr__(self):
        return "Light(type={0}, pos={1}, color={2})".format(
            self.getLightType(), self.position, self.color)

    @protected
    def _markDirty(self):
        """ Marks the light as dirty, it will get updated at the beginning of
        the next frame """
        print "Mark light dirty!"

