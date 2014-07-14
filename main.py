
"""


RenderPipeline example

This is a sample how you could integrate the Pipeline to your
current project. It shows the basic functions of the Pipeline.

"""


# Don't generate that annoying .pyc files
import sys
sys.dont_write_bytecode = True


import math
from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFile, Vec3, OmniBoundingVolume

from Cython.MovementController import MovementController
from Cython.RenderingPipeline import RenderingPipeline
from Cython.PointLight import PointLight
from Cython.BetterShader import BetterShader
from Cython.DebugObject import DebugObject
from Cython.FirstPersonController import FirstPersonCamera
from Cython.Globals import Globals

class Main(ShowBase, DebugObject):

    """ This is the render pipeline testing showbase """

    def __init__(self):
        DebugObject.__init__(self, "Main")

        # Load engine configuration
        self.debug("Loading panda3d configuration from configuration.prc ..")
        loadPrcFile("configuration.prc")

        # Init the showbase
        ShowBase.__init__(self)

        # Store globals, as cython can't handle them 
        Globals.load(self)

        # Create the render pipeline, that's really everything!
        self.debug("Creating pipeline")
        self.renderPipeline = RenderingPipeline(self)
        self.renderPipeline.loadSettings("pipeline.ini")
        self.renderPipeline.create()

        # Load some demo source
        # self.sceneSource = "Demoscene.ignore/export/SceneV1.egg"
        self.sceneSource = "Scene/Scene4.egg"
        self.usePlane = False

        self.debug("Loading Scene '" + self.sceneSource + "' ..")
        self.scene = self.loader.loadModel(self.sceneSource)
        # self.scene.flattenStrong()

        # Load ground plane if configured
        if self.usePlane:
            self.groundPlane = self.loader.loadModel("Scene/Plane.egg")
            self.groundPlane.setPos(0, 0, -0.1)
            self.groundPlane.setScale(2.0)
            self.groundPlane.setTwoSided(True)
            self.groundPlane.flattenStrong()
            self.groundPlane.reparentTo(self.scene)

        # Some artists really don't know about backface culling -.-
        # self.scene.setTwoSided(True)

        self.debug("Flattening scene and parenting to render")
        # self.scene.flattenStrong()
        self.scene.reparentTo(self.render)

        # Create movement controller (Freecam)
        self.controller = MovementController(self)
        self.controller.setInitialPosition(Vec3(-30, 30, 25), Vec3(0, 0, 0))
        self.controller.setup()

        # Create movement controller (First-Person)
        # self.mouseLook = FirstPersonCamera(self, self.camera, self.render)
        # self.mouseLook.start()

        # Hotkey to reload all shaders
        self.accept("r", self.setShaders)

        # Attach update task
        self.addTask(self.update, "update")

        # Store initial light positions for per-frame animations
        self.lights = []
        self.initialLightPos = []

        colors = [
            Vec3(1, 0, 0),
            Vec3(0, 1, 0),
            Vec3(0, 0, 1),
            Vec3(1, 1, 0),

            Vec3(1, 0, 1),
            Vec3(0, 1, 1),
            Vec3(1, 0.5, 0),
            Vec3(0, 0.5, 1.0),
        ]

        # Add some shadow casting lights
        for i in range(8):
            # break
            angle = float(i) / 8.0 * math.pi * 2.0

            pos = Vec3(math.sin(angle) * 10.0, math.cos(angle) * 10.0, 12)
            # pos = Vec3( (i-3.5)*15.0, 9, 5.0)
            light = PointLight()
            light.setRadius(30.0)
            # light.setColor(Vec3(2))
            light.setColor(colors[i]*2.0)
            light.setPos(pos)
            light.setShadowMapResolution(2048)
            light.setCastsShadows(True)

            # add light
            self.renderPipeline.addLight(light)
            self.lights.append(light)
            self.initialLightPos.append(pos)

        # Add even more normal lights
        for x in range(64):
            for y in range(64):
                break
                angle = float(x + y * 4) / 16.0 * math.pi * 2.0
                light = PointLight()
                light.setRadius(30.0)
                light.setColor(
                    Vec3(math.sin(angle) * 0.5 + 0.5, 
                        math.cos(angle) * 0.5 + 0.5, 0.5) * 0.5)
                # light.setColor(Vec3(0.5))
                initialPos = Vec3(
                    (float(x) - 2.0) * 10.0, (float(y) - 2.0) * 10.0, 5.0)
                initialPos = Vec3(0,0,1)
                light.setPos(initialPos)
                self.initialLightPos.append(initialPos)
                self.renderPipeline.addLight(light)
                self.lights.append(light)

        # ambient = PointLight()
        # ambient.setRadius(30.0)
        # ambient.setPos(Vec3(10, 10, 10))
        # ambient.setColor(Vec3(1.0))
        # self.renderPipeline.addLight(ambient)

        # self.loadLights("Scene.ignore/Street-LightData.egg")

        # create skybox

        self.loadSkybox()

        # set default object shaders
        self.setShaders()

    def loadLights(self, scene):
        model = self.loader.loadModel(scene)
        lights = model.findAllMatches("**/PointLight*")

        for prefab in lights:
            light = PointLight()
            light.setRadius(prefab.getScale().x*1.2)
            light.setColor(Vec3(2.0,1.8,0.7))
            light.setPos(prefab.getPos() + Vec3(0,0,6))
            light.setShadowMapResolution(1024 + 512)
            light.setCastsShadows(True)
            # light.attachDebugNode(self.render)
            self.renderPipeline.addLight(light)

            print "Adding:",prefab.getPos(), prefab.getScale()


    def loadSkybox(self):
        """ Loads the sample skybox. Will get replaced later """
        self.skybox = self.loader.loadModel("Skybox/Skybox")
        self.skybox.setScale(1000)
        self.skybox.reparentTo(self.render)

    def setShaders(self):
        """ Sets all shaders """
        self.debug("Reloading Shaders ..")

        if self.renderPipeline:
            self.scene.setShader(
                self.renderPipeline.getDefaultObjectShader(False))
            self.renderPipeline.debugReloadShader()

        self.skybox.setShader(BetterShader.load(
            "Shader/Skybox.vertex", "Shader/Skybox.fragment"))

    def update(self, task=None):
        """ Main update task """

        # self.debug("\n"*20)

        # import time
        # time.sleep(0.3)

        # return task.cont

        if True:
            animationTime = self.taskMgr.globalClock.getFrameTime() * 0.6

            # displace every light every frame - performance test!
            for i, light in enumerate(self.lights):
                lightAngle = float(math.sin(i * 1253325.0)) * \
                    math.pi * 2.0 + animationTime * 1.0
                initialPos = self.initialLightPos[i]
                light.setPos(initialPos + Vec3(math.sin(lightAngle) * 5.0,
                                               math.cos(lightAngle) * 5.0,
                                               math.sin(math.cos(lightAngle * 1.523) * 1.7)))
        if task is not None:
            return task.cont


app = Main()
app.run()
