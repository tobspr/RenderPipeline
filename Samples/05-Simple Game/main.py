

# First, we have to insert the pipeline path to the python path
import sys
sys.path.insert(0, '../../')

# Now import the pipeline
from Code.RenderingPipeline import RenderingPipeline


from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from panda3d.core import *
from math import sin, cos, pi

from Code.SpotLight import SpotLight

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

        # Disable scattering
        self.renderPipeline.settings.enableScattering = False

        # Now create the pipeline
        self.renderPipeline.create()

        # Load skybox
        self.skybox = self.renderPipeline.getDefaultSkybox()
        self.skybox.reparentTo(render)


        base.disableMouse()

        self.scene = loader.loadModel("models/level_b1.bam")
        self.scene.reparentTo(render)

        base.cam.setPos(0, 0, 15)
        base.cam.lookAt(0,5,5)

        self.actor = render.attachNewNode("actor")

        self.actorModel = Actor('models/male.egg', {
          'walk':'models/male2_walk.egg',
        })
        self.actorModel.setScale(0.03)
        self.actorModel.setH(-90)
        self.actorModel.reparentTo(self.actor)
        self.actorModel.loop("walk")

        self.accept("w", self.setMovementX, [1])
        self.accept("w-repeat", self.setMovementX, [1])
        self.accept("w-up", self.setMovementX, [0])

        self.accept("a", self.setMovementY, [1])
        self.accept("a-repeat", self.setMovementY, [1])
        self.accept("a-up", self.setMovementY, [0])
        self.accept("d", self.setMovementY, [-1])
        self.accept("d-repeat", self.setMovementY, [-1])
        self.accept("d-up", self.setMovementY, [0])


        # Create a light at the camera position
        light = SpotLight()
        light.setPos(Vec3(0,0,20))
        light.lookAt(Vec3(0,0,0))
        light.setColor(Vec3( 1.0, 0.5, 0.3) * 0.5)
        light.setNearFar(1.0, 50)
        light.setFov(140)
        light.setIESProfile("SoftArrow")
        light.setShadowMapResolution(8192)
        light.setCastsShadows(True)
        self.renderPipeline.addLight(light)
        self.playerLight = light

        self.movement = [0, 0]

        self.addTask(self.update, "update")

        # Call this to tell the pipeline that the scene is done loading
        self.renderPipeline.onSceneInitialized()

        self.accept("r", self.renderPipeline.reloadShaders)


    def setMovementX(self, directionX):
        self.movement[0] = directionX

    def setMovementY(self, directionY):
        self.movement[1] = directionY

    def update(self, task):
        
        hprV = self.movement[1] * globalClock.getDt() * 80.0
        self.actor.setH(self.actor.getH() + hprV)

        actorH = self.actor.getH() / 360.0 * 2.0 * pi

        velocityX = self.movement[0] * cos(actorH)
        velocityY = self.movement[0] * sin(actorH)

        self.actor.setPos(self.actor.getPos() - Vec3(velocityX, velocityY, 0) * globalClock.getDt() * 1.7)


        base.cam.setPos(self.actor.getPos() + Vec3(cos(actorH)*3,sin(actorH)*3, 3))
        base.cam.lookAt(self.actor.getPos() + Vec3(0,0,2.5))

        # self.playerLight.setPos(self.actor.getPos() + Vec3(0, 0, 20))
        # self.playerLight.lookAt(self.actor.getPos())
        


        return task.cont



# Create a new instance and run forever
app = App()
app.run()
