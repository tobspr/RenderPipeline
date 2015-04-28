# Don't generate .pyc files
import sys
sys.path.insert(0, "../../")

import os
sys.dont_write_bytecode = True


import math
import struct

from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFile, Vec3
from panda3d.core import Texture
from panda3d.core import Shader

from Code.MovementController import MovementController
from Code.RenderingPipeline import RenderingPipeline
from Code.PointLight import PointLight
from Code.DirectionalLight import DirectionalLight
from Code.DebugObject import DebugObject
from Code.FirstPersonController import FirstPersonCamera
from Code.GlobalIllumination import GlobalIllumination

from Code.GUI.BetterOnscreenImage import BetterOnscreenImage
from Code.GUI.BetterSlider import BetterSlider
from Code.GUI.BetterOnscreenText import BetterOnscreenText
from Code.GUI.UIWindow import UIWindow

class Main(ShowBase, DebugObject):

    """ This is the material explorer. You can try different materials"""

    def __init__(self):
        DebugObject.__init__(self, "Main")

        self.debug("Bit System =", 8 * struct.calcsize("P"))

        # Load engine configuration
        self.debug("Loading panda3d configuration from configuration.prc ..")
        loadPrcFile("../../Config/configuration.prc")

        # Init the showbase
        ShowBase.__init__(self)

        # Create the render pipeline
        self.debug("Creating pipeline")
        self.renderPipeline = RenderingPipeline(self)

        # Set a write directory, where the shader cache and so on is stored
        # self.renderPipeline.getMountManager().setWritePath(writeDirectory)
        self.renderPipeline.getMountManager().setBasePath("../../")       
        self.renderPipeline.loadSettings("../../Config/pipeline.ini")

        # Create the pipeline, and enable scattering
        self.renderPipeline.create()
        self.renderPipeline.enableDefaultEarthScattering()

        # Load some demo source
        self.sceneSource = "Models/SmoothCube/Cube.bam"

        # Load scene from disk
        self.debug("Loading Scene '" + self.sceneSource + "'")
        self.model = self.loader.loadModel(self.sceneSource)
        self.scene = render.attachNewNode("Scene")
        self.model.reparentTo(self.scene)
        self.model.setZ(1.0)

        # Wheter to use a ground floor
        self.usePlane = True
        self.sceneWireframe = False

        # Flatten scene
        self.scene.flattenStrong()

        # Load ground plane if configured
        if self.usePlane:
            self.groundPlane = self.loader.loadModel(
                "Models/Plane/Model.egg.bam")
            self.groundPlane.setPos(0, 0, 0)
            self.groundPlane.setScale(2.0)
            self.groundPlane.setTwoSided(True)
            self.groundPlane.flattenStrong()
            self.groundPlane.reparentTo(self.scene)


        # Prepare textures with SRGB format
        self.prepareSRGB(self.scene)

        # Create movement controller (Freecam)
        self.controller = MovementController(self)
        self.controller.setInitialPosition(
            Vec3(0, -5, 5.0), Vec3(0, 0, 5))
        self.controller.setup()

        # Hotkey for wireframe
        self.accept("f3", self.toggleSceneWireframe)

        # Hotkey to reload all shaders
        self.accept("r", self.setShaders)

        # Create a sun light
        dPos = Vec3(60, 30, 100)
        dirLight = DirectionalLight()
        dirLight.setDirection(dPos)
        dirLight.setShadowMapResolution(2048)
        dirLight.setAmbientColor(Vec3(0.0, 0.0, 0.0))
        dirLight.setPos(dPos)
        dirLight.setColor(Vec3(3))
        dirLight.setPssmTarget(base.cam, base.camLens)
        dirLight.setPssmDistance(50.0)
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

        # Load skyboxn
        self.skybox = self.renderPipeline.getDefaultSkybox()
        self.skybox.reparentTo(render)

        # Set default object shaders
        self.setShaders(refreshPipeline=False)

        self.createGUI()

    def createGUI(self):
        self.slider_opts = {
            "roughness": {
                "name": "Roughness",
                "min": 0.0001,
                "max": 1.0,
                "default": 0.4,
            },
            "metallic": {
                "name": "Metallic",
                "min": 0.0001,
                "max": 1.0,
                "default": 0.0,
            },
            "specular": {
                "name": "Specular",
                "min": 0.0001,
                "max": 1.0,
                "default": 0.5,
            },
            "basecolor_r": {
                "name": "Base Color [Red]",
                "min": 0.0001,
                "max": 1.0,
                "default": 1.0,
                "color": Vec3(1,0.2,0.2)
            },
            "basecolor_g": {
                "name": "Base Color [Green]",
                "min": 0.0001,
                "max": 1.0,
                "default": 1.0,
                "color": Vec3(0.6,1.0,0.2)
            },
            "basecolor_b": {
                "name": "Base Color [Blue]",
                "min": 0.0001,
                "max": 1.0,
                "default": 1.0,
                "color": Vec3(0.2,0.6,1)
            },

        }

        self.sliderOrder = ["roughness", "metallic", "specular", "", "basecolor_r", "basecolor_g", "basecolor_b"]


        self.guiParent = UIWindow(
            "Material Explorer", 280, 400)
        self.guiParent.getNode().setPos(self.win.getXSize() - 340, 0, -120)

        self.windowNode = self.guiParent.getContentNode()
        currentY = 5

        for name in self.sliderOrder:
            if name == "":
                currentY += 30
                continue
            opts = self.slider_opts[name]
            opts["slider"] = BetterSlider(
                x=20, y=currentY+20, size=230, minValue=opts["min"],maxValue=opts["max"], value=opts["default"], parent=self.windowNode, callback=self.materialOptionChanged)

            col = Vec3(1.0)
            if "color" in opts:
                col = opts["color"]

            opts["label"] = BetterOnscreenText(x=20, y=currentY,
                                           text=opts["name"], align="left", parent=self.windowNode,
                                           size=15, color=col)

            opts["value_label"] = BetterOnscreenText(x=250, y=currentY,
                                           text=str(opts["default"]), align="right", parent=self.windowNode,
                                           size=15, color=Vec3(0.6),mayChange=True)
            currentY += 50

    def materialOptionChanged(self):
        container = self.model

        for name, opt in self.slider_opts.items():
            container.setShaderInput("opt_" + name, opt["slider"].getValue())
            opt["value_label"].setText("{:0.4f}".format(opt["slider"].getValue()))
        


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

    def setShaders(self, refreshPipeline=True):
        """ Sets all shaders """
        self.debug("Reloading Shaders ..")

        if self.renderPipeline:
            self.scene.setShader(
                self.renderPipeline.getDefaultObjectShader(False))

            self.model.setShader(Shader.load(Shader.SLGLSL, 
                "DefaultObjectShader/vertex.glsl",
                "dynamicMaterialFragment.glsl"))

            if refreshPipeline:
                self.renderPipeline.reloadShaders()

        if self.skybox:
            self.skybox.setShader(Shader.load(Shader.SLGLSL, 
                "DefaultObjectShader/vertex.glsl", "Skybox/fragment.glsl"))

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
