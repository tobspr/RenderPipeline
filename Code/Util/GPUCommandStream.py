

from DebugObject import DebugObject

class GPUCommandStream:

    """ Class which offers an interface to the gpu. Classes can push commands
    to the stream, which will get executed on the gpu """

    def __init__(self):
        DebugObject.__init__(self, "GPUCommandStream")
        