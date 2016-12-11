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

from panda3d.core import Vec3, Material, Vec4

from rpcore.rpobject import RPObject

class MaterialAPI(RPObject):
    """ Interface for creating and modifying materials """

    SM_DEFAULT = 0
    SM_EMISSIVE = 1
    SM_CLEARCOAT = 2
    SM_TRANSPARENT = 3
    SM_SKIN = 4
    SM_FOLIAGE = 5

    @classmethod
    def make_material(cls, basecolor=Vec3(0.8), specular_ior=0.8):
        pass

    @classmethod
    def make_emissive(cls, basecolor=Vec3(0.8), emissive_factor=0.2, exact=False):
        """ Creates a new emissive material """
        m = Material()
        if not exact:
            m.set_base_color(Vec4(basecolor * emissive_factor, 1))
        else:
            m.set_base_color(Vec4(basecolor / 5000.0, 1))
        m.set_emission(Vec4(cls.SM_EMISSIVE, 0, 0, 0))
        m.set_roughness(1.0)
        m.set_refractive_index(1.5)
        m.set_metallic(0)
        return m    

    @classmethod
    def get_shading_model(cls, m):
        """ Extracts the shading model of a given material """
        return m.get_emission().x
