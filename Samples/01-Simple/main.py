

# First, we have to insert the pipeline path to the python path
import sys
sys.path.insert(0, '../../')

# Now import the pipeline
from Code.RenderingPipeline import RenderingPipeline
from Code.MovementController import MovementController

from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFile, Vec3

# Create a showbase class
class App(ShowBase):

    def __init__(self):

        # Load the default configuration.prc. This is recommended, as it
        # contains some important panda options
        loadPrcFile("../../Config/configuration.prc")

        # Init the showbase
        ShowBase.__init__(self)

        # Create a new pipeline instance
        self.renderPipeline = RenderingPipeline(self)

        # Set the base path for the pipeline. This is required as we are in
        # a subdirectory
        self.renderPipeline.getMountManager().setBasePath("../../")

        # Also set the write path
        self.renderPipeline.getMountManager().setWritePath("../../Temp/")

        # Load the default settings
        self.renderPipeline.loadSettings("../../Config/pipeline.ini")

        # Now create the pipeline
        self.renderPipeline.create()

        # Load the skybox
        self.skybox = self.renderPipeline.getDefaultSkybox()
        self.skybox.reparentTo(render)


        # Create the default movement controler
        self.controller = MovementController(self)
        self.controller.setInitialPositionHpr(
            Vec3(-2.5, -10.5, 7.5), Vec3(0, -14, 0))
        self.controller.setup()

        # At this point we are done with the initialization. Now you want to
        # load your scene, and create the game logic. 


        # Call this to tell the pipeline that the scene is done loading
        self.renderPipeline.onSceneInitialized()

# Create a new instance and run forever
app = App()
app.run()
