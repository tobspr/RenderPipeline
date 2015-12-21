"""






-------------------------------------------------------------------------------
--
--   WARNING
--
--   This file exists for testing purposes only!
--   It is not supposed to be run by the user. Please have a look at the samples
--   provided at Samples/.
--
--
-------------------------------------------------------------------------------





"""


# Disable the "xxx has no yyy member" error, pylint seems to be unable to detect
# the properties of a nodepath
# pylint: disable=E1101

from __future__ import print_function

import sys
import getpass
from random import random, randint, seed

from direct.showbase.ShowBase import ShowBase
from panda3d.core import Vec3

from __init__ import *
from Code.Util.MovementController import MovementController


# This check is required, because many people downloading the pipeline think this
# is the mainfile, while its only my main testing file. So this check here
# is to avoid confusion.
if len(sys.argv) != 2 or sys.argv[1] != "dev":
    if getpass.getuser() != "tspringe":
        print("This file is not meant to be run by the user!")
        print("Please have a look at the samples located at Samples/")
        sys.exit(0)


class MainApp(ShowBase):

    """ Main Testing Showbase """

    def __init__(self):

        self.render_pipeline = RenderPipeline(self)

        # Set the base path and mount the directories
        self.render_pipeline.get_mount_manager().set_write_path("Temp")
        self.render_pipeline.get_mount_manager().disable_cleanup()
        self.render_pipeline.get_mount_manager().mount()

        # Load the default prc file and settings
        self.render_pipeline.load_settings("Config/pipeline.yaml")

        # Create the pipeline
        self.render_pipeline.create()

        # profile = self.render_pipeline.load_ies_profile("Data/IESProfiles/Defined.ies")

        plane = self.loader.loadModel("Data/BuiltinModels/Plane/Plane.bam")
        plane.set_scale(6.0)
        plane.reparent_to(self.render)

        # Load some models, most of them are not included in the repository
        # model = self.loader.loadModel("Models/MaterialTester.ignore/Scene.bam")
        # model = loader.loadModel("Models/HDRTest/Scene.bam")
        # model = loader.loadModel("Models/Head/Scene.bam")
        # model = loader.loadModel("Models/Head/Hand.bam")
        # model = loader.loadModel("Models/SimpleShapes/Sphere.bam")
        # model = loader.loadModel("Models/UVTest/Scene.bam")
        # model = loader.loadModel("Models/SimpleShapes/Wall.bam")
        # model = loader.loadModel("Models/Test.ignore/Statue.bam")
        # model = loader.loadModel("Models/Test.ignore/Car0.bam")
        # model = loader.loadModel("Models/DemoTerrain/Scene.bam")
        # model = loader.loadModel("Models/DemoScene/Scene.bam")
        # model = loader.loadModel("Models/Sponza.ignore/Scene.bam")
        model = self.loader.loadModel("box")
        # model.flatten_strong()

        if False:
            self.render.set_shader_input("roughness", 1.0)
            self.render.set_shader_input("metallic", 0.0)
            self.render.set_shader_input("specular", 0.05)

            for roughness in range(11):
                for metallic in range(2):
                    placeholder = self.render.attach_new_node("placeholder")
                    placeholder.set_pos((roughness-5) * 2.3, (metallic) * 5.3, 0)
                    placeholder.set_shader_input("roughness", roughness / 10.0)
                    placeholder.set_shader_input("metallic", metallic / 1.0)
                    model.instance_to(placeholder)
        else:
            model.reparent_to(self.render)

        self.render_pipeline.create_default_skybox()

        # Add some random lights
        sqr = 4
        seed(3)
        for x in range(sqr):
            for y in range(sqr):

                if randint(0, 1) == 0:
                    light = PointLight()
                    light.set_color(0, 1, 0)
                else:
                    light = SpotLight()
                    light.set_direction(0, 0, -1)
                    light.set_fov(90)
                    light.set_color(1, 0, 0)

                pos_x, pos_y = (x-sqr//2) * 10.0, (y-sqr//2) * 10.0
                light.set_pos(Vec3(pos_x, pos_y, 7.0))
                # light.set_color(Vec3(random(), random(), random()) * 2)
                light.set_radius(15.0)
                self.render_pipeline.add_light(light)

        if True:
            test_light = SpotLight()
            test_light.set_pos(0, -20, 6)
            test_light.set_radius(40)
            test_light.set_color(Vec3(171, 238, 255) / 255.0 * 2.0)
            test_light.look_at(0, 0, 6)
            test_light.set_fov(30)
            # test_light.set_ies_profile(0)
            test_light.set_casts_shadows(True)
            self.render_pipeline.add_light(test_light)

        # lights = model.find_all_matches("**/Light*")

        # for light_prefab in lights:
        #     light = SpotLight()
        #     light.set_pos(light_prefab.get_pos())
        #     light.set_radius(17)
        #     light.set_color(Vec3(1.0, 1.0, 1.3) * 2.0)
        #     light.set_direction(0, 0, -1)
        #     light.set_fov(90)
        #     light.set_ies_profile(profile)
        #     self.render_pipeline.add_light(light)

        # Init movement controller
        self.controller = MovementController(self)
        self.controller.set_initial_position(Vec3(10), Vec3(0))
        # self.controller.set_initial_position(Vec3(0, 0, 100), Vec3(0))
        self.controller.setup()

MainApp().run()
