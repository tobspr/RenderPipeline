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

from panda3d.core import Vec3

from direct.stdpy.file import join

from rpcore.globals import Globals
from rpcore.rpobject import RPObject
from rpcore.loader import RPLoader
from rpcore.native import SphereLight, RectangleLight, SpotLight, TubeLight
from rpcore.util.material_api import MaterialAPI


class LightGeometry(RPObject):
    """ Helper class for creating appropriate geometry for lights """

    # Material for the backfaces of lights, for example for rectangle lights.
    BACKFACE_MATERIAL = MaterialAPI.make_emissive(
        name="LightBackfaceMaterial", basecolor=Vec3(0), exact=True)

    # Special name for the nodes, to avoid getting exported by the mitsuba exporter
    DEBUG_GEOMETRY_NAME = "LightDebugGeometry"

    # Path to the visualization models
    MODEL_PATH = "/$$rp/data/builtin_models/lights/"

    @classmethod
    def make(cls, light):
        """ Creates the appropriate geometry for the given light, and
        returns it. The geometry will already be parented to Globals.render.
        Notice that the geometry does not react to changes to the light.
        If you want it to change dynamically, remove the node whenever the
        light changes, and call this method again """
        if isinstance(light, SphereLight):
            return cls._make_sphere_light(light)
        elif isinstance(light, RectangleLight):
            return cls._make_rectangle_light(light)
        elif isinstance(light, SpotLight):
            return cls._make_spot_light(light)
        elif isinstance(light, TubeLight):
            return cls._make_tube_light(light)
        else:
            cls.error("Unkown light type:", light.__class__)

    @classmethod
    def _make_sphere_light(cls, light):
        """ Internal method to create the geometry for a sphere light """
        model = RPLoader.load_model(join(cls.MODEL_PATH, "sphere.bam"))
        MaterialAPI.force_apply_material(model, cls._make_light_material(light))
        model.reparent_to(Globals.base.render)
        model.set_pos(light.pos)
        model.set_scale(light.sphere_radius)
        model.set_name(cls.DEBUG_GEOMETRY_NAME)
        return model

    @classmethod
    def _make_rectangle_light(cls, light):
        """ Internal method to create the geometry for a rectangle light """
        parent = Globals.base.render.attachNewNode(cls.DEBUG_GEOMETRY_NAME)
        for side in [1, -1]:
            model = RPLoader.load_model(join(cls.MODEL_PATH, "rectangle.bam"))
            if side == 1:
                material = cls._make_light_material(light)
            else:
                material = cls.BACKFACE_MATERIAL
            MaterialAPI.force_apply_material(model, material)
            model.look_at(light.up_vector.cross(light.right_vector) * side, light.up_vector)
            model.set_sz(light.up_vector.length())
            model.set_sx(light.right_vector.length())
            model.reparent_to(parent)
            model.set_pos(light.pos)
            model.set_name(cls.DEBUG_GEOMETRY_NAME)
            return parent

    @classmethod
    def _make_tube_light(cls, light):
        """ Internal method to make a tube light """
        model = RPLoader.load_model(join(cls.MODEL_PATH, "tube.bam"))

        # Create sphere on both ends
        left = model.find("**/TubeEndLeft")
        left.set_y(light.tube_length / 2 - light.tube_radius)
        left.set_scale(light.tube_radius)
        left.set_name(cls.DEBUG_GEOMETRY_NAME)

        right = model.find("**/TubeEndRight")
        right.set_y(-light.tube_length / 2 + light.tube_radius)
        right.set_scale(light.tube_radius)
        right.set_name(cls.DEBUG_GEOMETRY_NAME)

        # Scale cylinder in the mid
        mid = model.find("**/TubeMid")
        mid.set_scale(light.tube_radius, light.tube_radius,
                      light.tube_length / 2 - light.tube_radius)
        mid.set_name(cls.DEBUG_GEOMETRY_NAME)

        MaterialAPI.force_apply_material(model, cls._make_light_material(light))
        model.look_at(light.tube_direction)
        model.reparent_to(Globals.base.render)
        model.set_pos(light.pos)
        model.set_name(cls.DEBUG_GEOMETRY_NAME)
        return model

    @classmethod
    def _make_spot_light(cls, light):  # pylint: disable=unused-argument
        """ Internal method to create the geometry for a spot light """
        cls.warn("TODO: Implement spot lights in light ")
        return Globals.base.render.attach_new_node(cls.DEBUG_GEOMETRY_NAME)

    @classmethod
    def _make_light_material(cls, light):
        """ Internal method to create the correct emissive material for the
        given light """
        basecolor = light.color * light.intensity_luminance
        return MaterialAPI.make_emissive(
            name="LightGeomMaterial", basecolor=basecolor, exact=True)
