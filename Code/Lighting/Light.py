
from panda3d.core import Vec3

from ..Util.DebugObject import DebugObject

class Light(DebugObject):

    """ This is the abstract base class for all Lights """

    # Light Types
    LTNone = 0
    LTPointLight = 1

    def __init__(self):
        DebugObject.__init__(self, "Light")
        self.dirty = False
        self.position = Vec3(0)
        self.color = Vec3(0)

    def getLightType(self):
        """ Returns the type of the light, should be overriden by subclasses """
        raise NotImplementedError()

    def addToStream(self, command):
        """ Adds the light to a command stream, subclasses should implement this,
        and call this method, then add their own data """
        
        # Light Header
        command.pushInt(self.getSlot())
        command.pushInt(self.getLightType())

        # Light Data start
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

    def isDirty(self):
        """ Returns whether the light needs an update """
        return self.dirty

    def setSlot(self, slot):
        """ Internal method to set a slot """
        self.__slot = slot

    def hasSlot(self):
        """ Internal method to check whether a slot is assigned """
        return hasattr(self, "__slot")

    def getSlot(self):
        """ Returns the slot if it is assigned, otherwise throws an exception """
        return self.__slot

    def removeSlot(self):
        """ Removes the slot assigned to the light """
        del self.__slot

    
    def __repr__(self):
        """ Returns a representative string of the light """
        return "Light(type={0}, pos={1}, color={2})".format(
            self.getLightType(), self.position, self.color)

    
    def _markDirty(self):
        """ Marks the light as dirty, it will get updated at the beginning of
        the next frame """
        self.dirty = True
