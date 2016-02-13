

# Disable the "xxx has no yyy member" error, pylint seems to be unable to detect
# the properties of a nodepath
# pylint: disable=E1101

from __future__ import print_function

import os
os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "."))

import sys
import math
sys.path.insert(0, os.getcwd())
from random import random, randint, seed

from direct.showbase.ShowBase import ShowBase
from panda3d.core import Vec3, load_prc_file_data

from __init__ import *
from six.moves import range
from code.util.movement_controller import MovementController


class MainApp(ShowBase):

    """ Main Testing Showbase """

    def __init__(self):

        load_prc_file_data("", """
        fullscreen #f
        win-size 1920 1080
        window-title Render Pipeline by tobspr
        icon-filename Data/GUI/icon.ico
        """)
        self.render_pipeline = RenderPipeline(self)

        # Set the base path and mount the directories
        self.render_pipeline.mount_mgr.write_path = "temp"
        self.render_pipeline.mount_mgr.do_cleanup = False
        self.render_pipeline.mount_mgr.mount()

        # Create the pipeline
        self.render_pipeline.create()

        profile = self.render_pipeline.load_ies_profile("data/ies_profiles/defined.ies")

        plane = self.loader.loadModel("data/builtin_models/plane/plane.bam")
        plane.set_scale(10.0)
        plane.reparent_to(self.render)

        # Load some models, most of them are not included in the repository
        # model = loader.loadModel("models/sponza/scene.bam")

        # model = loader.loadModel("Models/CornelBox/Scene.bam")
        model = loader.loadModel("panda")
        # model.flatten_strong()

        # model.set_two_sided(True)

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
        sqr = 0
        seed(3)
        for x in range(sqr):
            for y in range(sqr):

                if randint(0, 1) == 0:
                    light = PointLight()
                    light.color = (1, 1, 1.2)
                else:
                    light = SpotLight()
                    light.direction = (random()*0.6 - 0.3, random()*0.6 - 0.3, -1)
                    light.fov = 110
                    light.color = Vec3(1, 1, 1.2) * 75.0

                pos_x, pos_y = (x-sqr//2) * 14.0, (y-sqr//2) * 14.0
                pos_x += 25
                light.pos = Vec3(pos_x, pos_y, 12.0)

                light.color = Vec3(0.6 + random(), 0.6 + random(), 0.8 + random())
                # light.casts_shadows = True
                light.radius = 45.0
                light.lumens = 20
                # light.shadow_map_resolution = 512
                self.render_pipeline.add_light(light)

        if False:
            for i in range(1):
                test_light = SpotLight()
                test_light.pos = ((i)*4, 10, 10)
                test_light.radius = 25.0
                test_light.color = Vec3(171, 238, 255) / 255.0 * 20.0
                test_light.fov = 80
                test_light.ies_profile = profile
                test_light.near_plane = 3.0
                # test_light.casts_shadows = True
                test_light.look_at(0, 0, 0)

                self.render_pipeline.add_light(test_light)
                self.test_light = test_light
                test_light.shadow_map_resolution = 2048

        # Init movement controller
        self.controller = MovementController(self)
        self.controller.set_initial_position(Vec3(10), Vec3(0))
        self.controller.setup()

MainApp().run()
