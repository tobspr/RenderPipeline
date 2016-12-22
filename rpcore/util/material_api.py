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

from panda3d.core import Vec3, Material, Vec4, MaterialAttrib

from rpcore.rpobject import RPObject


class MaterialAPI(RPObject):
    """ Interface for creating and modifying materials """

    # All shading models
    SM_DEFAULT = 0
    SM_EMISSIVE = 1
    SM_CLEARCOAT = 2
    SM_TRANSPARENT_GLASS = 3
    SM_SKIN = 4
    SM_FOLIAGE = 5
    SM_TRANSPARENT_EMISSIVE = 6

    # Internal factor for scaling emissive materials
    EMISSIVE_SCALE = 5000.0

    # All modes which are transparent
    TRANSPARENT_MODELS = [SM_TRANSPARENT_GLASS, SM_TRANSPARENT_EMISSIVE]

    @classmethod
    def make_material(cls, basecolor=Vec3(0.8), specular_ior=0.8):
        """ Creates a new material with the given properties """
        raise NotImplementedError("TODO")

    @classmethod
    def make_emissive(cls, name="GeneratedMaterial", basecolor=Vec3(0.8),
                      emissive_factor=0.2, exact=False):
        """ Creates a new emissive material. If exact is set to True,
        the material will be configured to represent the given basecolor
        1:1 on screen, this is useful for the light debug geometry. """
        material = Material(name)
        if not exact:
            material.set_base_color(Vec4(basecolor * emissive_factor, 1))
        else:
            material.set_base_color(Vec4(basecolor / cls.EMISSIVE_SCALE, 1))
        material.set_emission(Vec4(cls.SM_EMISSIVE, 0, 0, 0))
        material.set_roughness(1.0)
        material.set_refractive_index(1.5)
        material.set_metallic(0)
        return material

    @classmethod
    def make_regular(cls, name="GeneratedMaterial", basecolor=Vec3(0.8), metallic=False,
                     specular_ior=1.51, roughness=0.3):
        """ Creates a new regular material with the default shading model. Notice
        that when metallic is set to True, the specular_ior parameter will be
        ignored. """
        if metallic:
            if specular_ior != 1.51:
                RPObject.global_error("MaterialAPI", "Specular ior specified for metallic "
                                      "material! Resetting to ior of 1.51")
                specular_ior = 1.51
        material = Material(name)
        material.set_base_color(basecolor)
        material.set_metallic(1.0 if metallic else 0.0)
        material.set_roughness(roughness)
        material.set_refractive_index(specular_ior)
        material.set_emission(Vec4(cls.SM_DEFAULT, 0, 0, 0))
        return material

    @classmethod
    def make_transparent(cls, name="GeneratedMaterial", roughness=0.3, alpha=0.3):
        material = cls.make_regular(roughness=roughness)
        material.set_emission(Vec4(cls.SM_TRANSPARENT_GLASS, 0, alpha, 0))
        return material

    @classmethod
    def get_shading_model(cls, material):
        """ Extracts the shading model of a given material """
        return material.get_emission().x

    @classmethod
    def force_apply_material(cls, nodepath, material):
        """ Forcedly overrides the material on the given nodepath, by applying
        it to the material attribute of every geom. """
        for geom_np in nodepath.find_all_matches("**/+GeomNode"):
            geom_node = geom_np.node()
            for i in range(geom_node.get_num_geoms()):
                geom_state = geom_node.get_geom_state(i)
                new_state = geom_state.set_attrib(MaterialAttrib.make(material))
                geom_node.set_geom_state(i, new_state)
        nodepath.set_material(material, 1000)
