
from ..Util.DebugObject import DebugObject
from GPUCommand import GPUCommand

class GPUCommandQueue(DebugObject):

    """ This class offers an interface to the gpu, allowing commands to be
    pushed to a queue which then get executed on the gpu """

    def __init__(self):
        DebugObject.__init__(self, "GPUCommandQueue")

    def clearQueue(self):
        pass

    def addCommand(self, command):
        assert(isinstance(command, GPUCommand))
        self.debug("Adding command", command)