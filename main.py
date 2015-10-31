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




import sys


# This check is required, because many people downloading the pipeline think this
# is the mainfile, while its only my main testing file. So this check here
# is to avoid confusion.
if len(sys.argv) != 2 or sys.argv[1] != "dev":
    print("This file is not meant to be run by the user!")
    print("Please have a look at the samples located at Samples/")
    sys.exit(0)

from random import random


from direct.showbase.ShowBase import ShowBase
from panda3d.core import load_prc_file, Vec3

sys.path.insert(0, "../")
from RenderPipeline import *
from RenderPipeline.Code.Util.MovementController import MovementController


class MainApp(ShowBase):

    def __init__(self):


        self.render_pipeline = RenderPipeline(self)
        self.render_pipeline.set_default_loading_screen()

        # Set the base path and mount the directories
        self.render_pipeline.get_mount_manager().set_base_path(".")
        self.render_pipeline.get_mount_manager().set_write_path("Temp")
        self.render_pipeline.get_mount_manager().disable_cleanup()
        self.render_pipeline.get_mount_manager().mount()

        # Load the default prc file and settings
        load_prc_file("Config/configuration.prc")
        self.render_pipeline.load_settings("Config/pipeline.ini")

        # Create the pipeline
        self.render_pipeline.create()


        render.set_shader_input("roughness", 0.0)
        render.set_shader_input("metallic", 0.0)
        render.set_shader_input("specular", 0.1)


        plane = loader.loadModel("Models/GroundPlane/Scene.bam")
        plane.set_scale(10.0)
        plane.reparent_to(render)
        
        # Load some models
        model = loader.loadModel("Models/MaterialTester.ignore/Scene.bam")
        model.flatten_strong()


        for roughness in range(0, 11):
            for metallic in range(0, 2):
                placeholder = render.attach_new_node("placeholder")
                placeholder.set_pos( (roughness-5) * 2.3, (metallic) * 5.3, 0)
                placeholder.set_shader_input("roughness", roughness / 10.0)
                placeholder.set_shader_input("metallic", metallic / 1.0)
                placeholder.set_shader_input("specular", 0.5)
                model.instance_to(placeholder)

        self.render_pipeline.create_default_skybox()
        self.lights = []

        # Add some random lights
        sqr = 8
        for x in range(sqr):
            for y in range(sqr):
                light = PointLight()
                light.set_pos( Vec3(x-sqr//2 + random(), y-sqr//2 + random(), 1.2 + random()) * 4)
                light.set_color(Vec3(0.5) * (0.2 + random()) ) 
                # light.set_color(random(), random(), random()) 
                light.set_radius(15)
                self.lights.append(light)
                self.render_pipeline.add_light(light)
        
        # Init movement controller
        self.controller = MovementController(self)
        self.controller.set_initial_position(Vec3(10), Vec3(0))
        self.controller.setup()

        self.addTask(self.update_task, "update_task")
        self.dummy_light = None

    def update_task(self, task=None):

        if self.dummy_light:
            self.render_pipeline.remove_light(self.dummy_light)

        # self.dummy_light = PointLight()
        # self.dummy_light.set_pos(random()*10, random()*10, 5)
        # self.dummy_light.set_color( Vec3(0.2, 0.6, 1.0) * 3.0 )
        # self.dummy_light.set_radius(30)
        # self.render_pipeline.add_light(self.dummy_light)

        # for light in self.lights:
            # light.set_color(random(), random(), random())
            # light.set_pos(Vec3(random(), random(), 1.0) * 30 - 15)
        return task.cont


MainApp().run()
