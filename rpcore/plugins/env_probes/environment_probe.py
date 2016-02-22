"""

RenderPipeline

Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

import struct
from panda3d.core import TransformState, Vec3, Mat4

from rpcore.rp_object import RPObject

class EnvironmentProbe(RPObject):
    """ Simple class, representing an environment probe """

    def __init__(self, priority=0):
        """ Inits a new environment probe, priority controls how important the
        probe is (default is 0, higher values mean more important) """
        RPObject.__init__(self)
        self.priority = priority
        self.index = -1
        self.last_update = -1
        self.transform = TransformState.make_identity()

    def set_pos(self, *args):
        """ Sets the probe position """
        self.transform = self.transform.set_pos(Vec3(*args))

    def set_hpr(self, *args):
        """ Sets the probe rotation """
        self.transform = self.transform.set_hpr(Vec3(*args))

    def set_scale(self, *args):
        """ Sets the probe scale """
        self.transform = self.transform.set_scale(Vec3(*args))

    @property
    def matrix(self):
        """ Returns the matrix of the probe """
        return self.transform.get_mat()

    def write_to_buffer(self, buffer_ptr):
        """ Writes the probe to a given byte buffer """
        data, mat = [], Mat4(self.matrix)
        mat.invert_in_place()
        for i in range(4):
            for j in range(4):
                data.append(mat.get_cell(i, j))
        byte_data = struct.pack("f" * 16, *data)

        # 1) 4 = sizeof float, 2) 16 = floats per cubemap
        bytes_per_probe = 4 * 16
        buffer_ptr.set_subdata(
            self.index * bytes_per_probe, bytes_per_probe, byte_data)
