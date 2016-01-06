
from __future__ import print_function
from six.moves import range
 
import struct

class GPUCommand(object):

    CMD_invalid = 0
    CMD_store_light = 1
    CMD_remove_light = 2
    CMD_store_source = 3
    CMD_remove_sources = 4

    def __init__(self, command_type):
        self._command_type = command_type
        self._current_index = 0
        self._data = [0.0] * 32
        self.push_int(command_type)

    def push_int(self, v):
        self.push_float(float(v))

    def push_float(self, v):
        if self._current_index >= 32:
            print("GPUCommand: out of bounds!")
            return
        self._data[self._current_index] = float(v)
        self._current_index += 1

    def push_vec3(self, v):
        self.push_float(v.get_x())
        self.push_float(v.get_y())
        self.push_float(v.get_z())

    def push_vec4(self, v):
        self.push_vec3(v)
        self.push_float(v.get_w())

    def push_mat4(self, v):
        for i in range(4):
            for j in range(4):
                self.push_float(v.get_cell(i, j))

    @staticmethod
    def get_uses_integer_packing():
        return False

    def write_to(self, dest, command_index):
        data = struct.pack("f"*32, *self._data)
        offset = command_index * 32 * 4
        dest.set_subdata(offset, 32 * 4, data)

    def write(self, out=None):
        print("GPUCommand(type=", self._command_type, "size=", self._current_index,")")
        print("Data:", ', '.join([str(i) for i in self._data]))
