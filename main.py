"""









RenderPipeline testing file

If you are looking for Code Examples, look at Samples/. This file is for
testing purposes only, and also not very clean coded!




"""


# Don't generate that annoying .pyc files
import sys
sys.dont_write_bytecode = True


import math
import struct

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

        self.debug("Bit System =", 8 * struct.calcsize("P"))

        # Load engine configuration
        self.debug("Loading panda3d configuration from configuration.prc ..")
        loadPrcFile("Config/configuration.prc")

        # Init the showbase
        ShowBase.__init__(self)

        # Create the render pipeline
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

        # add scattering support
        self.renderPipeline.settings.enableScattering = True

        self.renderPipeline.create()

         ####### END OF RENDER PIPELINE SETUP #######

        # Load some demo source
        self.sceneSource = "Demoscene.ignore/sponza.egg.bam"
        # self.sceneSource = "Demoscene.ignore/occlusionTest/Model.egg"
        # self.sceneSource = "Demoscene.ignore/lost-empire/Model.egg"
        # self.sceneSource = "Models/PSSMTest/Model.egg.bam"
        # self.sceneSource = "Scene.ignore/Car.bam"
        # self.sceneSource = "Demoscene.ignore/GITest/Model.egg"
        # self.sceneSource = "Models/Raventon/Model.egg"
        # self.sceneSource = "BlenderMaterialLibrary/MaterialLibrary.egg"
        self.usePlane = False

        self.debug("Loading Scene '" + self.sceneSource + "'")
        self.scene = self.loader.loadModel(self.sceneSource)

        # self.scene.setScale(0.05)
        self.scene.flattenStrong()
        # Load ground plane if configured
        if self.usePlane:
            self.groundPlane = self.loader.loadModel(
                "Models/Plane/Model.egg.bam")
            self.groundPlane.setPos(0, 0, -0.01)
            self.groundPlane.setScale(2.0)
            self.groundPlane.setTwoSided(True)
            self.groundPlane.flattenStrong()
            self.groundPlane.reparentTo(self.scene)

        # Some artists really don't know about backface culling -.-
        # self.scene.setTwoSided(True)

        self.debug("Flattening scene and parenting to render")

        # Required for tesselation
        # self.convertToPatches(self.scene)

        self.scene.reparentTo(self.render)

        self.debug("Preparing SRGB ..")
        self.prepareSRGB(self.scene)
        # Create movement controller (Freecam)
        self.controller = MovementController(self)
        self.controller.setInitialPosition(
            Vec3(23.6278, -52.0626, 9.021), Vec3(-30, 0, 0))
        self.controller.setup()

        self.sceneWireframe = False

        self.accept("f3", self.toggleSceneWireframe)

        # Hotkey to reload all shaders
        self.accept("r", self.setShaders)

        # Attach update task
        self.addTask(self.update, "update")

        # Store initial light positions for per-frame animations
        self.lights = []
        self.initialLightPos = []

        vplHelpLights = [
            Vec3(-66.1345, -22.2243, 33.5399),
            Vec3(63.6877, 29.0491, 33.3335)
        ]

        vplHelpLights = [
            Vec3(0, 0, 5)
        ]

        # dPos = Vec3(-100, -100, 100)
        dPos = Vec3(60, 30, 100)
        dirLight = DirectionalLight()
        dirLight.setDirection(dPos)
        dirLight.setShadowMapResolution(2048)
        dirLight.setAmbientColor(Vec3(0.1,0.1,0.1))
        dirLight.setCastsShadows(True)
        dirLight.setPos(dPos)
        dirLight.setColor(Vec3(4))
        self.renderPipeline.addLight(dirLight)
        self.initialLightPos.append(dPos)
        self.lights.append(dirLight)
        self.dirLight = dirLight

        for pos in vplHelpLights:
            break
            helpLight = PointLight()
            helpLight.setRadius(100)
            helpLight.setPos(pos)
            helpLight.setColor(Vec3(2))
            helpLight.setShadowMapResolution(128)
            helpLight.setCastsShadows(True)
            self.renderPipeline.addLight(helpLight)
            self.initialLightPos.append(pos)
            self.lights.append(helpLight)

        earthScattering = Scattering()

        scale = 100000
        earthScattering.setSettings({
            "atmosphereOffset": Vec3(0, 0, - (6360.0 + 9.5) * scale),
            # "atmosphereOffset": Vec3(0),
            "atmosphereScale": Vec3(scale)
        })

        earthScattering.precompute()

        # hack in scattering for testing
        self.renderPipeline.lightingComputeContainer.setShaderInput(
            "transmittanceSampler", earthScattering.getTransmittanceResult())
        self.renderPipeline.lightingComputeContainer.setShaderInput(
            "inscatterSampler", earthScattering.getInscatterTexture())

        self.skybox = None
        self.loadSkybox()

        # set default object shaders
        self.setShaders(refreshPipeline=False)

        earthScattering.bindTo(
            self.renderPipeline.lightingComputeContainer, "scatteringOptions")

        self.renderPipeline.guiManager.demoSlider.node[
            "command"] = self.setSunPos

        # self.sunSlider = BetterSlider(
            # x=300, y=100, size=200, parent=self.pixel2d,
            # callback=self.setSunPos)

    def setSunPos(self):
        rawValue = self.renderPipeline.guiManager.demoSlider.node["value"]
        # rawValue = rawValue / 100.0 * 2.0 * math.pi

        # v = Vec3(math.sin(rawValue) * 100.0, math.cos(rawValue) * 100.0, 100)
        dPos = Vec3(0, rawValue, 100)
        self.dirLight.setPos(dPos)
        self.dirLight.setDirection(dPos)

    def toggleSceneWireframe(self):
        """ Toggles the scene rendermode """
        self.sceneWireframe = not self.sceneWireframe

        if self.sceneWireframe:
            self.scene.setRenderModeWireframe()
        else:
            self.scene.clearRenderMode()

    def prepareSRGB(self, np):
        """ Sets the correct texture format for all textures found in <np> """
        for tex in np.findAllTextures():

            baseFormat = tex.getFormat()

            if baseFormat == Texture.FRgb:
                tex.setFormat(Texture.FSrgb)
            elif baseFormat == Texture.FRgba:
                tex.setFormat(Texture.FSrgbAlpha)
            else:
                print "Unkown texture format:", baseFormat
                print "\tTexture:", tex

            # tex.setMinfilter(Texture.FTLinearMipmapLinear)
            # tex.setMagfilter(Texture.FTLinear)
            tex.setAnisotropicDegree(16)

    def loadLights(self, scene):
        """ Loads lights from a .egg. Lights should be empty objects (blender) """
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

    def setShaders(self, refreshPipeline=True):
        """ Sets all shaders """
        self.debug("Reloading Shaders ..")

        # return
        if self.renderPipeline:
            self.scene.setShader(
                self.renderPipeline.getDefaultObjectShader(False))

            if refreshPipeline:
                self.renderPipeline.reloadShaders()

        if self.skybox:
            self.skybox.setShader(BetterShader.load(
                "Shader/DefaultObjectShader/vertex.glsl", "Shader/Skybox/fragment.glsl"))

    def convertToPatches(self, model):
        """ Converts a model to patches. This is REQUIRED before beeing able
        to use it """
        self.debug("Converting to patches ..")
        for node in model.find_all_matches("**/+GeomNode"):
            geom_node = node.node()
            num_geoms = geom_node.get_num_geoms()
            for i in range(num_geoms):
                geom_node.modify_geom(i).make_patches_in_place()

        self.debug("Converted!")

    def update(self, task=None):
        """ Main update task """

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
