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

        # Set the base path and mount the directories
        self.render_pipeline.get_mount_manager().set_base_path(".")
        self.render_pipeline.get_mount_manager().mount()

        # Load the default prc file and settings
        load_prc_file("Config/configuration.prc")
        self.render_pipeline.load_settings("Config/pipeline.ini")

        # Create the pipeline
        self.render_pipeline.create()



        # Load some models

        plane = loader.loadModel("Models/GroundPlane/Scene.bam")
        plane.reparent_to(render)
        self.render_pipeline.create_default_skybox()


        # Add some random lights
        for i in range(64):
            light = PointLight()
            light.set_pos( Vec3(random(), random(), 1.0) * 30 - 15)
            light.set_color(random(), random(), random()) 
            light.set_radius(20)
            self.render_pipeline.add_light(light)
        

        # Init movement controller
        self.controller = MovementController(self)
        self.controller.set_initial_position(Vec3(10), Vec3(0))
        self.controller.setup()





MainApp().run()