
from ..Util.DebugObject import DebugObject


class GPUCommand(DebugObject):

    CMD_INVALID = 0
    CMD_STORE_LIGHT = 1

    """ This represents a command to be executed on the gpu. Data can be attached
    by using the pushXXX methods. """

    def __init__(self, command_type=CMD_INVALID):
        DebugObject.__init__(self, "GPUCommand")
        self._command_type = command_type
        self._command_data = [command_type]

    def get_data_size(self):
        """ Returns the length of the command, including the command header """
        return len(self._command_data)

    def get_data(self):
        """ Returns a readonly handle to the data """
        return self._command_data

    def enforce_width(self, width, fill_value=0.0):
        """ Forces the command to have a given width, if its smaller the command
        gets padded, if its bigger an exception is thrown """
        # Increase width by the size of the command header
        width += 1
        if len(self._command_data) > width:
            raise Exception("GPU Command exceeds enforced size")
        self._command_data += [fill_value] * (width - len(self._command_data))

    def push_int(self, val):
        """ Adds a new integer to the command """
        self._command_data.append(val)

    def push_float(self, val):
        """ Adds a new float to the command """
        self._command_data.append(val)

    def push_vec3(self, val):
        """ Adds a new 3 dimensional vector to the command """
        self._command_data += list(val)

    def push_vec4(self, val):
        """ Adds a new 4 dimensional vector to the command """
        self._command_data += list(val)

    def push_mat4(self, val):
        """ Adds a new 4x4 matrix to the command """
        self.debug("PUSH_MAT4", val)
        raise NotImplementedError()

    def __repr__(self):
        """ Returns a representative string of the command """
        return "GPUCommand(type={0}, len={1})".format(
            self._command_type, self.get_data_size())
