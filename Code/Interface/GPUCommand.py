
from ..Util.DebugObject import DebugObject
from ..Util.FunctionDecorators import protected

class GPUCommand(DebugObject):

    CMD_INVALID = 0
    CMD_STORE_LIGHT = 1

    """ This represents a command to be executed on the gpu. Data can be attached
    by using the pushXXX methods. """

    def __init__(self, command_type=CMD_INVALID):
        DebugObject.__init__(self, "GPUCommand")
        self.command_type = command_type
        self.command_data = [command_type]
        # self.debug("Creating new command of type", command_type)

    def getDataSize(self):
        """ Returns the length of the command, including the command header """
        return len(self.command_data)

    def getData(self):
        """ Returns a readonly handle to the data """
        return self.command_data

    def enforceWidth(self, width, fillValue = 0.0):
        """ Forces the command to have a given width, if its smaller the command
        gets padded, otherwise an exception is thrown """
        # Increase width by the size of the command header
        width += 1 
        if len(self.command_data) > width:
            raise Exception("GPU Command exceeds enforced size")
        self.command_data += [0] * (width - len(self.command_data))

    def pushInt(self, val):
        """ Adds a new integer to the command """
        self.command_data.append(val)
    
    def pushFloat(self, val):
        """ Adds a new float to the command """
        self.command_data.append(val)

    def pushVec3(self, val):
        """ Adds a new 3 dimensional vector to the command """
        self.command_data += list(val)

    def pushVec4(self, val):
        """ Adds a new 4 dimensional vector to the command """
        self.command_data += list(val)

    def pushMat4(self, val):
        """ Adds a new 4x4 matrix to the command """
        self.debug("PUSH_MAT4", val)
        raise NotImplementedError()

    @protected
    def __repr__(self):
        """ Returns a representative string of the command """
        return "GPUCommand(type={0}, len={1})".format(self.command_type, self.getDataSize())
