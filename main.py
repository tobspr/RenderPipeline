
"""


RenderPipeline example

This is a sample how you could integrate the Pipeline to your
current project. It shows the basic functions of the Pipeline.
Not that this file is not very clean coded, as it is the
main testing file. 

"""


# Don't generate that annoying .pyc files
import sys
sys.dont_write_bytecode = True


import math
import shutil
import struct
import tempfile
import atexit
import os

from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFile, Vec3
from panda3d.core import Texture

from Code.MovementController import MovementController
from Code.RenderingPipeline import RenderingPipeline
from Code.PointLight import PointLight
from Code.DirectionalLight import DirectionalLight
from Code.BetterShader import BetterShader
from Code.DebugObject import DebugObject
from Code.FirstPersonController import FirstPersonCamera
from Code.Scattering import Scattering


class Main(ShowBase, DebugObject):

    """ This is the render pipeline testing showbase """

    def __init__(self):
        DebugObject.__init__(self, "Main")

        self.debug("Bitness =", 8 * struct.calcsize("P"))

        # Load engine configuration
        self.debug("Loading panda3d configuration from configuration.prc ..")
        loadPrcFile("Config/configuration.prc")

        # Init the showbase
        ShowBase.__init__(self)

        ####### RENDER PIPELINE SETUP #######
        # Create the render pipeline, that's really everything!
        self.debug("Creating pipeline")
        self.renderPipeline = RenderingPipeline(self)
        self.renderPipeline.loadSettings("Config/pipeline.ini")

        # Uncomment to use temp directory
        # writeDirectory = tempfile.mkdtemp(prefix='Shader-tmp')
        # writeDirectory = "Temp/"
        # Clear write directory when app exits
        # atexit.register(os.remove, writeDirectory)
        # Set a write directory, where the shader cache and so on is stored
        # self.renderPipeline.getMountManager().setWritePath(writeDirectory)




        self.renderPipeline.getMountManager().setBasePath(".")
        self.renderPipeline.create()

         ####### END OF RENDER PIPELINE SETUP #######

        # Load some demo source
        # self.sceneSource = "Demoscene.ignore/sponza.egg.bam"
        self.sceneSource = "Models/PSSMTest/Model.egg.bam"
        # self.sceneSource = "Models/Raventon/Model.egg"
        # self.sceneSource = "BlenderMaterialLibrary/MaterialLibrary.egg"
        self.usePlane = False

        self.debug("Loading Scene '" + self.sceneSource + "'")
        self.scene = self.loader.loadModel(self.sceneSource)

        # self.scene.setScale(0.05)
        # self.scene.flattenStrong()
        # Load ground plane if configured
        if self.usePlane:
            self.groundPlane = self.loader.loadModel("Models/Plane/Model.egg")
            self.groundPlane.setPos(0, 0, -0.01)
            self.groundPlane.setScale(2.0)
            self.groundPlane.setTwoSided(True)
            self.groundPlane.flattenStrong()
            self.groundPlane.reparentTo(self.scene)

        # Some artists really don't know about backface culling -.-
        # self.scene.setTwoSided(True)

        self.debug("Flattening scene and parenting to render")
        # self.convertToPatches(self.scene)
        self.scene.flattenStrong()

        self.scene.reparentTo(self.render)

        self.prepareSRGB(self.scene)

        # self.render2d.setShader(BetterShader.load("Shader/GUI/vertex.glsl", "Shader/GUI/fragment.glsl"))

        # Create movement controller (Freecam)
        self.controller = MovementController(self)
        # self.controller.setInitialPosition(Vec3(-30, 30, 25), Vec3(0, 0, 0))
        self.controller.setInitialPosition(Vec3(3, 3, 3), Vec3(0, 0, 1))
        self.controller.setup()
        # base.disableMouse()
        # base.camera.setPos(0.988176, 2.53928, 2.75053)
        # base.camera.setHpr(-57.69, -5.67802, 0)

        # base.accept("c", PStatClient.connect)
        # base.accept("v", self.bufferViewer.toggleEnable)

        # Create movement controller (First-Person)
        # self.mouseLook = FirstPersonCamera(self, self.camera, self.render)
        # self.mouseLook.start()

        # self.scene.node().setAttrib(ShadeModelAttrib.make(ShadeModelAttrib.MSmooth),
        # 100000)

        self.sceneWireframe = False

        self.accept("f3", self.toggleSceneWireframe)

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

        res = [128, 256, 512, 1024]

        # Add some shadow casting lights
        for i in range(4):
            break
            angle = float(i) / 4.0 * math.pi * 2.0

            # pos = Vec3(math.sin(angle) * 10.0 + 5, math.cos(angle) * 20.0, 30)
            pos = Vec3((i - 1.5) * 15.0, 9, 5.0)
            # pos = Vec3(8)
            # print "POS:",pos
            light = PointLight()
            light.setRadius(150.0)
            light.setColor(Vec3(1))
            # light.setColor(colors[i]*1.0)
            light.setPos(pos)
            light.setShadowMapResolution(res[i])
            light.setCastsShadows(True)

            # add light
            self.renderPipeline.addLight(light)
            self.lights.append(light)
            self.initialLightPos.append(pos)

            # break

        # Add even more normal lights
        for x in range(4):
            for y in range(4):
                break
                angle = float(x + y * 4) / 16.0 * math.pi * 2.0
                light = PointLight()
                light.setRadius(10.0)
                light.setColor(
                    Vec3(math.sin(angle) * 0.5 + 0.5,
                         math.cos(angle) * 0.5 + 0.5, 0.5) * 0.5)
                # light.setColor(Vec3(0.5))
                initialPos = Vec3(
                    (float(x) - 2.0) * 15.0, (float(y) - 2.0) * 15.0, 5.0)
                # initialPos = Vec3(0,0,1)
                light.setPos(initialPos)
                self.initialLightPos.append(initialPos)
                self.renderPipeline.addLight(light)
                self.lights.append(light)

        contrib = 1.0

        # for x, y in [(-1.1, -0.9), (-1.2, 0.8), (1.3, -0.7), (1.4, 0.6)]:
        for x in xrange(4):
            break
        # for x,y in [(0,0)]:
            ambient = PointLight()
            ambient.setRadius(120.0)

            initialPos = Vec3(float(x - 2) * 21.0, 0, 60)
            ambient.setPos(initialPos)
            ambient.setColor(Vec3(1.0))
            ambient.setShadowMapResolution(1024)
            ambient.setCastsShadows(True)
            self.lights.append(ambient)
            self.initialLightPos.append(initialPos)
            # ambient.attachDebugNode(render)

            self.renderPipeline.addLight(ambient)

            # contrib *= 0.4
            # break

        dirLight = DirectionalLight()
        dirLight.setDirection(Vec3(50, 100, 50))
        # dirLight.setPos(Vec3(50, 100, 150))
        dirLight.setColor(Vec3(18,17.5,15))
        self.renderPipeline.addLight(dirLight)


        d = Scattering()
        d.setSettings({
                "atmosphereOffset": Vec3(0,0, 6360.0 + 9.5),
                "atmosphereScale": Vec3(1000.0)
            })
        d._setInputs(self.renderPipeline.lightingComputeContainer, "scatteringOptions")
        d.precompute()
        
        # hack in for testing
        self.renderPipeline.lightingComputeContainer.setShaderInput(
            "transmittanceSampler", d.getTransmittanceResult())
        self.renderPipeline.lightingComputeContainer.setShaderInput(
            "inscatterSampler", d.getInscatterTexture())

        self.skybox = None
        self.loadSkybox()

        # set default object shaders
        self.setShaders()
       

    def toggleSceneWireframe(self):
        self.sceneWireframe = not self.sceneWireframe

        if self.sceneWireframe:
            self.scene.setRenderModeWireframe()
        else:
            self.scene.clearRenderMode()

    def prepareSRGB(self, np):
        for tex in np.findAllTextures():

            baseFormat = tex.getFormat()

            if baseFormat == Texture.FRgb:
                tex.setFormat(Texture.FSrgb)
            elif baseFormat == Texture.FRgba:
                tex.setFormat(Texture.FSrgbAlpha)
            else:
                print "Unkown texture format:", baseFormat
                print "\tTexture:", tex

            tex.setMinfilter(Texture.FTLinearMipmapLinear)
            tex.setMagfilter(Texture.FTLinear)
            tex.setAnisotropicDegree(16)

        # for stage in np.findAllTextureStages():
        #     print stage, stage.getMode()

    def loadLights(self, scene):
        model = self.loader.loadModel(scene)
        lights = model.findAllMatches("**/PointLight*")

        return
        for prefab in lights:
            light = PointLight()
            # light.setRadius(prefab.getScale().x)
            light.setRadius(40.0)
            light.setColor(Vec3(2))
            light.setPos(prefab.getPos())
            light.setShadowMapResolution(2048)
            light.setCastsShadows(False)
            # light.attachDebugNode(self.render)
            self.renderPipeline.addLight(light)
            print "Adding:", prefab.getPos(), prefab.getScale()
            self.lights.append(light)
            self.initialLightPos.append(prefab.getPos())
            self.test = light

            # break

    def loadSkybox(self):
        """ Loads the sample skybox. Will get replaced later """
        self.skybox = self.loader.loadModel("Models/Skybox/Model.egg.bam")
        self.skybox.setScale(40000)
        self.skybox.reparentTo(self.render)

    def setShaders(self):
        """ Sets all shaders """
        self.debug("Reloading Shaders ..")

        # return
        if self.renderPipeline:
            self.scene.setShader(
                self.renderPipeline.getDefaultObjectShader(False))
            self.renderPipeline.reloadShaders()

        if self.skybox:
            self.skybox.setShader(BetterShader.load(
                "Shader/DefaultObjectShader/vertex.glsl", "Shader/Skybox/fragment.glsl"))

    def convertToPatches(self, model):
        self.debug("Converting to patches ..")
        for node in model.find_all_matches("**/+GeomNode"):
            geom_node = node.node()
            num_geoms = geom_node.get_num_geoms()
            for i in range(num_geoms):
                geom_node.modify_geom(i).make_patches_in_place()

        self.debug("Converted!")

    def update(self, task=None):
        """ Main update task """

        # Simulate 30 FPS
        # import time
        # time.sleep( max(0.0, 0.033))
        # time.sleep(-0.2)
        # return task.cont

        if False:
            animationTime = self.taskMgr.globalClock.getFrameTime() * 1.0

            # displace every light every frame - performance test!
            for i, light in enumerate(self.lights):
                lightAngle = float(math.sin(i * 1253325.0)) * \
                    math.pi * 2.0 + animationTime * 1.0
                initialPos = self.initialLightPos[i]
                light.setPos(initialPos + Vec3(math.sin(lightAngle) * 1.0,
                                               math.cos(lightAngle) * 1.0,
                                               math.sin(animationTime) * 1.0))
        if task is not None:
            return task.cont


app = Main()
app.run()
