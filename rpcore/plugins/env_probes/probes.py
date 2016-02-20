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

from panda3d.core import Vec3, BoundingBox, Texture, Vec4, GeomEnums
from rpcore.rp_object import RPObject
from rpcore.image import Image

class EnvironmentProbe(object):
    """ Simple class, representing an environment probe """

    def __init__(self, position, size, priority=0):
        """ Inits a new environment probe, position specifies the world space
        position, size specifies the dimensions of the probe and priority controls
        how important the probe is (default is 0, higher values mean more important) """
        self.position = position
        self.priority = priority
        self.size = size
        self.storage_tex_index = -1
        self.last_update = -1
        self.bounds = BoundingBox(position - size, position + size)

class ProbeManager(RPObject):
    """ Manages all environment probes """

    def __init__(self, resolution):
        self.probes = []
        self.resolution = resolution
        self._create_storage()

    def _create_storage(self):
        """ Creates the cubemap storage """
        self.storage_tex = Image("EnvmapStorage")
        self.storage_tex.setup_cube_map_array(self.resolution, 32, Texture.T_float, Texture.F_rgba16)
        self.storage_tex.set_clear_color(Vec4(0.0, 0.0, 0.1, 1.0))
        self.storage_tex.clear_image()

        self.cubemap_storage = Image("EnvmapData")
        self.cubemap_storage.setup_buffer_texture(32, Texture.T_float, Texture.F_rgba32, GeomEnums.UH_dynamic)
        self.cubemap_storage.set_clear_color(Vec4(0))
        self.cubemap_storage.clear_image()

    def add_probe(self, probe):
        """ Adds a new probe """
        self.probes.append(probe)

    def find_probe_to_update(self):
        """ Finds the next probe which requires an update, or returns None """
        if not self.probes:
            return None
        return self.probes[0]
