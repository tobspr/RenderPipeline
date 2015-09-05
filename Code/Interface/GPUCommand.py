
from ..Util.DebugObject import DebugObject

class GPUCommand(DebugObject):

    """ This represents a command to be executed on the gpu. Data can be attached
    by using the pushXXX methods. """

    def __init__(self):
        DebugObject.__init__(self, "GPUCommand")

    def pushInt(self, val):
        self.debug("PUSH_INT", val)
    
    def pushFloat(self, val):
        self.debug("PUSH_FLOAT", val)

    def pushVec3(self, val):
        self.debug("PUSH_VEC3", val)

    def pushVec4(self, val):
        self.debug("PUSH_VEC4", val)

    def pushMat4(self, val):
        self.debug("PUSH_MAT4", val)


