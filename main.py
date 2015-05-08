"""


RenderPipeline testing file

If you are looking for Code Examples, look at Samples/. This file is for
testing purposes only, and also not very clean coded!



"""


# Don't generate .pyc files
import sys
import os
sys.dont_write_bytecode = True


import math
import struct
from random import random
import copy

from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFile, Vec3, SamplerState
from panda3d.core import Texture
from panda3d.core import Shader, CullFaceAttrib, AntialiasAttrib

from Code.MovementController import MovementController
from Code.RenderingPipeline import RenderingPipeline
from Code.PointLight import PointLight
from Code.DirectionalLight import DirectionalLight
from Code.DebugObject import DebugObject
from Code.FirstPersonController import FirstPersonCamera
from Code.GlobalIllumination import GlobalIllumination
from Code.SpotLight import SpotLight
from Code.GUI.PipelineLoadingScreen import PipelineLoadingScreen



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


        # Show loading screen
        self.loadingScreen = PipelineLoadingScreen(self)
        self.loadingScreen.render()
        self.loadingScreen.setStatus("Creating pipeline")

        # Create the render pipeline
        self.debug("Creating pipeline")
        self.renderPipeline = RenderingPipeline(self)

        # Uncomment to use temp directory
        # writeDirectory = tempfile.mkdtemp(prefix='Shader-tmp')
        writeDirectory = "Temp/"

        # Clear write directory when app exits
        # atexit.register(os.remove, writeDirectory)

        # Set a write directory, where the shader cache and so on is stored
        #self.renderPipeline.getMountManager().setWritePath(writeDirectory)
        self.renderPipeline.getMountManager().setBasePath(".")
        
        # Load pipeline settings
        self.renderPipeline.loadSettings("Config/pipeline.ini")


        self.loadingScreen.setStatus("Compiling shaders")

        # Create the pipeline, and enable scattering
        self.renderPipeline.create()

        ####### END OF RENDER PIPELINE SETUP #######

        # Select demo scene here:

        # This sources are not included in the repo, for size reasons
        # self.sceneSource = "Demoscene.ignore/MasterSword/Scene.egg"
        # self.sceneSource = "Demoscene.ignore/MasterSword/Scene2.egg.bam"
        # self.sceneSource = "Demoscene.ignore/Couch2/Scene.egg"
        # self.sceneSource = "Demoscene.ignore/Couch/couch.egg.bam"
        # self.sceneSource = "Demoscene.ignore/LivingRoom/LivingRoom.egg"
        # self.sceneSource = "Demoscene.ignore/LivingRoom2/LivingRoom.egg"
        # self.sceneSource = "Demoscene.ignore/LostEmpire/Model.egg"
        # self.sceneSource = "Demoscene.ignore/SSLRTest/scene.egg"
        # self.sceneSource = "Demoscene.ignore/BMW/Bmw.egg"
        # self.sceneSource = "Demoscene.ignore/TransparencyTest/Scene.egg"


        # This sources are included in the repo
        # self.sceneSource = "Models/CornelBox/Model.egg"
        # self.sceneSource = "Models/HouseSet/Model.egg"
        # self.sceneSource = "Models/PSSMTest/Model.egg.bam"
        self.sceneSource = "Models/PBSTest/Scene.egg.bam"
        # self.sceneSource = "Models/HDRTest/Scene.egg"
        # self.sceneSource = "Models/GITestScene/Scene.egg"
        # self.sceneSource = "Models/VertexPerformanceTest/Scene.egg.bam"

        # self.sceneSource = "Toolkit/Blender Material Library/MaterialLibrary.egg.bam"
        


        # Select surrounding scene here
        self.sceneSourceSurround = None
        # self.sceneSourceSurround = "Demoscene.ignore/Couch/Surrounding.egg"
        # self.sceneSourceSurround = "Demoscene.ignore/LivingRoom/LivingRoom.egg"

        self.transparentObjects = []

        # Create a sun light
        dPos = Vec3(60, 30, 100)
        dirLight = DirectionalLight()
        dirLight.setDirection(dPos)
        dirLight.setShadowMapResolution(1024)
        dirLight.setPos(dPos)
        dirLight.setColor(Vec3(1))
        # dirLight.setColor(Vec3(0.3))
        dirLight.setPssmTarget(base.cam, base.camLens)
        dirLight.setCastsShadows(True)

        self.renderPipeline.addLight(dirLight)
        self.dirLight = dirLight
        sunPos = Vec3(56.7587, -31.3601, 189.196)
        self.dirLight.setPos(sunPos)
        self.dirLight.setDirection(sunPos)

        # Tell the GI which light casts the GI
        self.renderPipeline.setGILightSource(dirLight)

        # Slider to move the sun
        if self.renderPipeline.settings.displayOnscreenDebugger:
            self.renderPipeline.guiManager.demoSlider.node[
                "command"] = self.setSunPos
            self.renderPipeline.guiManager.demoSlider.node[
                "value"] = 80

            self.lastSliderValue = 0.0

        self.movingLights = []

        # Create some lights
        for i in xrange(5):
            pointLight = PointLight()

            radius = float(i) / 6.0 * 6.28 + 1.52
            xoffs = math.sin(radius) * 12.0
            yoffs = math.cos(radius) * 12.0

            # pointLight.setPos(Vec3(i*4.0 - 7.5, 1.5 + i, 12.0))
            pointLight.setPos(Vec3( xoffs, yoffs, 12))
            # pointLight.setColor(Vec3( abs(math.sin(radius) * 2.0), abs(math.cos(radius) * 2.0),1.0))
            pointLight.setColor(Vec3( 0.3, 0.75, 1.0))
            # pointLight.setColor(Vec3(1))
            # pointLight.setColor(Vec3( 1))
            # pointLight.setColor(Vec3( 1))
            # pointLight.setColor(Vec3( random(), random(), random()) * 0.2)

            pointLight.setShadowMapResolution(512)
            pointLight.setRadius(25)
            pointLight.setCastsShadows(True)
            # pointLight.attachDebugNode(render)
            self.renderPipeline.addLight(pointLight)

            self.movingLights.append(pointLight)

        # Create more lights
        for i in xrange(5):
            spotLight = PointLight()
            # spotLight = SpotLight()

            radius = float(i) / 5.0 * 6.28 + 5.22
            xoffs = math.sin(radius) * 15.0
            yoffs = math.cos(radius) * 15.0

            spotLight.setPos(Vec3( xoffs, yoffs, 12))

            # spotLight.setPos(Vec3(-10.0 + i * 2.0, 2.0, 4.0))
            # spotLight.setColor(Vec3(i,2-i,0))
            # spotLight.setColor(Vec3(0.2,0.6,1.0) * 0.2)
            spotLight.setColor(Vec3(0.2,0.6,1.0) * 0.05)
            # spotLight.setColor(Vec3( random(), random(), random()) * 0.1)

            # spotLight.setNearFar(1.0, 20.0)
            # spotLight.setDirection(Vec3(0, 90, 0))
            spotLight.setRadius(30)
            # spotLight.setCastsShadows(True)
            self.renderPipeline.addLight(spotLight)
            # spotLight.attachDebugNode(render)

        # Slow mode?
        # self.addTask(self.sleep, "sleep")
        self.addTask(self.update, "update")

        self.loadingScreen.setStatus("Loading scene")
        
        if True:
            # Show loading screen a bit
            self.doMethodLater(0.0, self.loadScene, "Load Scene")
        else:
            self.loadScene()



    def sleep(self, task):
        import time
        time.sleep(0.1)
        return task.cont


    def update(self, task):
        for idx, light in enumerate(self.movingLights):
            light.setZ(math.sin(idx +globalClock.getFrameTime())*2.0 + 13)

        return task.cont

    def loadScene(self, task=None):
        """ Starts loading the scene """
        # Load scene from disk
        self.debug("Loading Scene '" + self.sceneSource + "'")
        self.loader.loadModel(self.sceneSource, callback = self.onSceneLoaded)

    def onSceneLoaded(self, scene):

        self.debug("Successfully loaded scene")

        self.loadingScreen.setStatus("Loading skybox")

        self.scene = scene
        self.scene.prepareScene(self.win.getGsg())

        # Load surround scene
        if self.sceneSourceSurround is not None:
            self.debug("Loading Surround-Scene '" + self.sceneSourceSurround + "'")
            self.sceneSurround = self.loader.loadModel(self.sceneSourceSurround)
            self.sceneSurround.reparentTo(self.scene)


        # Performance testing

        if False:
            highPolyObj = self.scene.find("**/HighPolyObj")

            if highPolyObj is not None and not highPolyObj.isEmpty():
                highPolyObj.detachNode()
                self.loadingScreen.setStatus("Preparing Performance Test")

                for x in xrange(10):
                    for y in xrange(10):
                        copiedObj = copy.deepcopy(highPolyObj)
                        copiedObj.setColorScale(random(), random(), random(), 1)
                        copiedObj.reparentTo(self.scene)
                        copiedObj.setPos(x-5, y-5, 2)

        # Find transparent objects

        # self.transpObjRoot = render.attachNewNode("transparentObjects")
        # matches = self.scene.findAllMatches("**/T__*")
        # for match in matches:
        #     # match.reparentTo(self.transpObjRoot)
        #     self.transparentObjects.append(match)
        #     self.renderPipeline.prepareTransparentObject(match)
        #     # match.listTags()
        #     match.setAttrib(CullFaceAttrib.make(CullFaceAttrib.M_none))
        #     match.setColorScale(1,0,1, 1)

        # Wheter to use a ground floor
        self.usePlane = False
        self.sceneWireframe = False

        # Flatten scene?
        self.loadingScreen.setStatus("Optimizing Scene")

        # loader.asyncFlattenStrong(self.scene, inPlace=False, callback=self.onScenePrepared)
        self.onScenePrepared()

    def onScenePrepared(self, cb=None):

        # self.scene = cb
        self.scene.reparentTo(self.render)

        # Prepare textures with SRGB format
        self.prepareSRGB(self.scene)

        # Prepare MAterials
        self.renderPipeline.fillTextureStages(render)


        # Load ground plane if configured
        if self.usePlane:
            self.groundPlane = self.loader.loadModel(
                "Models/Plane/Model.egg.bam")
            self.groundPlane.setPos(0, 0, -0.0001)
            self.groundPlane.setScale(12.0)
            self.groundPlane.setTwoSided(True)
            self.groundPlane.flattenStrong()
            self.groundPlane.reparentTo(self.scene)


        # Some artists really don't know about backface culling
        # self.scene.setTwoSided(True)

        # Required for tesselation
        # self.convertToPatches(self.scene)


        # Hotkey for wireframe
        self.accept("f3", self.toggleSceneWireframe)

        # Hotkey to reload all shaders
        self.accept("r", self.setShaders)

        # For rdb
        self.accept("f12", self.screenshot)

        # Create movement controller (Freecam)
        self.controller = MovementController(self)
        self.controller.setInitialPosition(
            Vec3(0, -15, 25), Vec3(0, 0, 3))
        self.controller.setup()

        # self.fpCamera = FirstPersonCamera(self, self.cam, self.render)
        # self.fpCamera.start()

        # Load skybox
        self.skybox = self.renderPipeline.getDefaultSkybox()
        self.skybox.reparentTo(render)

        # Set default object shaders
        self.setShaders(refreshPipeline=False)

        # Hide loading screen
        self.loadingScreen.hide()


    def setSunPos(self):
        """ Sets the sun position based on the debug slider """

        radial = True
        rawValue = self.renderPipeline.guiManager.demoSlider.node["value"]
        diff = self.lastSliderValue - rawValue
        self.lastSliderValue = rawValue

        if radial:
            rawValue = rawValue / 100.0 * 2.0 * math.pi
            dPos = Vec3(
                math.sin(rawValue) * 100.0, math.cos(rawValue) * 100.0, 50)
            # dPos = Vec3(100, 100, (rawValue - 50) * 10.0)
        else:
            dPos = Vec3(30, (rawValue - 50) * 1.5, 30)

        if abs(diff) > 0.0001:
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

            # Only diffuse textures should be SRGB
            if "diffuse" in tex.getName().lower():
                # print "Preparing texture", tex.getName()
                if baseFormat == Texture.FRgb:
                    tex.setFormat(Texture.FSrgb)
                elif baseFormat == Texture.FRgba:
                    tex.setFormat(Texture.FSrgbAlpha)
                elif baseFormat == Texture.FSrgb or baseFormat == Texture.FSrgbAlpha:
                    # Format is okay already
                    pass
                else:
                    print "Unkown texture format:", baseFormat
                    print "\tTexture:", tex

            # All textures should have the correct filter modes
            tex.setMinfilter(Texture.FTLinearMipmapLinear)
            tex.setMagfilter(Texture.FTLinear)
            tex.setAnisotropicDegree(16)

    def loadLights(self, scene):
        """ Loads lights from a .egg. Lights should be empty objects (blender) """
        model = self.loader.loadModel(scene)
        lights = model.findAllMatches("**/PointLight*")

        for prefab in lights:
            light = PointLight()
            light.setRadius(prefab.getScale().x)
            light.setColor(Vec3(2))
            light.setPos(prefab.getPos())
            light.setShadowMapResolution(2048)
            light.setCastsShadows(False)
            self.renderPipeline.addLight(light)
            print "Adding Light:", prefab.getPos(), prefab.getScale()
            self.lights.append(light)
            self.initialLightPos.append(prefab.getPos())
            self.test = light

    def setShaders(self, refreshPipeline=True):
        """ Sets all shaders """
        self.debug("Reloading Shaders ..")

        if self.renderPipeline:

            for obj in self.transparentObjects:
                obj.setShader(
                    self.renderPipeline.getDefaultTransparencyShader(), 30)

            if refreshPipeline:
                self.renderPipeline.reloadShaders()

    def convertToPatches(self, model):
        """ Converts a model to patches. This is REQUIRED before beeing able
        to use it with tesselation shaders """
        self.debug("Converting model to patches ..")
        for node in model.find_all_matches("**/+GeomNode"):
            geom_node = node.node()
            num_geoms = geom_node.get_num_geoms()
            for i in range(num_geoms):
                geom_node.modify_geom(i).make_patches_in_place()

app = Main()
app.run()
