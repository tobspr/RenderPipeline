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


from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFile, Vec3, SamplerState
from panda3d.core import Texture
from panda3d.core import Shader, CullFaceAttrib

from Code.MovementController import MovementController
from Code.RenderingPipeline import RenderingPipeline
from Code.PointLight import PointLight
from Code.DirectionalLight import DirectionalLight
from Code.DebugObject import DebugObject
from Code.FirstPersonController import FirstPersonCamera
from Code.GlobalIllumination import GlobalIllumination



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

        # Uncomment to use temp directory
        # writeDirectory = tempfile.mkdtemp(prefix='Shader-tmp')
        writeDirectory = "Temp/"

        # Clear write directory when app exits
        # atexit.register(os.remove, writeDirectory)

        # Set a write directory, where the shader cache and so on is stored
        #self.renderPipeline.getMountManager().setWritePath(writeDirectory)
        self.renderPipeline.getMountManager().setBasePath(".")
        
         ####### END OF RENDER PIPELINE SETUP #######
        # Load some demo source
        # self.sceneSource = "Demoscene.ignore/sponza.egg.bam"
        # self.sceneSource = "Demoscene.ignore/occlusionTest/Model.egg"
        # self.sceneSource = "Demoscene.ignore/lost-empire/Model.egg"
        # self.sceneSource = "Models/PSSMTest/Model.egg.bam"
        # self.sceneSource = "Demoscene.ignore/GITest/Model.egg"
        # self.sceneSource = "Demoscene.ignore/PSSMTest/Model.egg.bam"
        # self.sceneSource = "Demoscene.ignore/Room/LivingRoom.egg"
        # self.sceneSource = "Models/CornelBox/Model.egg"
        # self.sceneSource = "Models/HouseSet/Model.egg"
        self.sceneSource = "Toolkit/Blender Material Library/MaterialLibrary.egg.bam"
        
        self.renderPipeline.loadSettings("Config/pipeline.ini")

        # Create the pipeline, and enable scattering
        self.renderPipeline.create()
        self.renderPipeline.enableDefaultEarthScattering()
        
        # Load scene from disk
        self.debug("Loading Scene '" + self.sceneSource + "'")
        self.scene = self.loader.loadModel(self.sceneSource)
        
        # Load transparent object
        # self.transparentObj = loader.loadModel("Models/SmoothCube/Cube.bam")
        # self.transparentObj = loader.loadModel("Demoscene.ignore/transparencyTest/scene.egg")
        self.transparentObj = loader.loadModel("panda")
        self.transparentObj.reparentTo(render)

        # self.transparentObj2.reparentTo(self.transparentObj)
        # self.transparentObj2.setPos(5,0, 0)
        self.transparentObj.setPos(0,0,2.01)
        # self.transparentObj.setScale(0.2)
        self.transparentObj.flattenStrong()

        self.transparentObj.setAttrib(CullFaceAttrib.make(CullFaceAttrib.M_none))
        # self.transparentObj.setDepthWrite(False)
        # self.transparentObj.setDepthTest(False)
        # self.transparentObj.setBin("transparent", 200)

        # Wheter to use a ground floor

        self.usePlane = False
        self.sceneWireframe = False

        # Flatten scene?
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

        # Some artists really don't know about backface culling
        # self.scene.setTwoSided(True)

        # Required for tesselation

        # self.convertToPatches(self.scene)

        self.scene.reparentTo(self.render)

        # Prepare textures with SRGB format
        self.prepareSRGB(self.scene)

        # Create movement controller (Freecam)wwww
        self.controller = MovementController(self)
        self.controller.setInitialPosition(
            Vec3(0, -5, 5.0), Vec3(0, 0, 5))
        self.controller.setup()

        # Hotkey for wireframe
        self.accept("f3", self.toggleSceneWireframe)

        # Hotkey to reload all shaders
        self.accept("r", self.setShaders)


        # for i in xrange(1):
        #     pointLight = PointLight()
        #     pointLight.setPos(Vec3( (i-1)*3, 0, 7))
        #     pointLight.setColor(Vec3(0.1))
        #     pointLight.setShadowMapResolution(1024)
        #     pointLight.setRadius(50)
        #     pointLight.setCastsShadows(True)
        #     # pointLight.attachDebugNode(render)
        #     self.renderPipeline.addLight(pointLight)

        # Create a sun light
        dPos = Vec3(60, 30, 100)
        dirLight = DirectionalLight()
        dirLight.setDirection(dPos)
        dirLight.setShadowMapResolution(2048)
        dirLight.setAmbientColor(Vec3(0.0, 0.0, 0.0))
        dirLight.setPos(dPos)
        dirLight.setColor(Vec3(3))
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
                "value"] = 20

            self.lastSliderValue = 0.0

        # Load skybox
        self.skybox = self.renderPipeline.getDefaultSkybox()
        self.skybox.reparentTo(render)

        # Set default object shaders
        self.setShaders(refreshPipeline=False)

        # Show windows
        # for window in base.graphicsEngine.getWindows():
            # print window.getName(), window.getSort()
    
        # self.addTask(self.sleep, "sleep")        

    def sleep(self, task):
        import time
        time.sleep(0.1)
        return task.cont

    def setSunPos(self):
        """ Sets the sun position based on the debug slider """

        radial = True
        rawValue = self.renderPipeline.guiManager.demoSlider.node["value"]
        diff = self.lastSliderValue - rawValue
        self.lastSliderValue = rawValue

        if radial:
            rawValue = rawValue / 100.0 * 2.0 * math.pi
            dPos = Vec3(
                math.sin(rawValue) * 100.0, math.cos(rawValue) * 100.0, 100)
            # dPos = Vec3(100, 100, (rawValue - 50) * 10.0)
        else:
            dPos = Vec3(30, (rawValue - 50) * 1.5, 100)

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
                print "Preparing texture", tex.getName()
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
            self.scene.setShader(
                self.renderPipeline.getDefaultObjectShader(False))
            self.transparentObj.setShader(
                self.renderPipeline.getDefaultTransparencyShader())



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
