 
def __init__(self, command_type):
    self._command_type = command_type
    self._data = [self._command_type] + [0.0] * 31
    self._current_index = 1

def print_data(self):
    print("GPUCommand(type=", self._command_type, "size=", self._current_index,")")
    print("DATA:", ', '.join([str(i) for i in self._data]))

def write_to(self, dest, command_index):

    data = struct.pack("f"*32, *self._data)
    offset = command_index * 32 * 4
    dest.set_subdata(offset, 32 * 4, data)
    
def push_int(self, v):
    self.push_float(float(v))

def push_float(self, v):
    if self._current_index >= 32:
        print("ERROR: GPUCommand out of bounds!")
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
    raise NotImplementedError("Not implemented yet!")
