# Don't generate .pyc files
import sys
sys.path.insert(0, "../../")

import os
sys.dont_write_bytecode = True


import math
import struct

from random import random

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

        # Load some demo source
        # self.sceneSource = "Models/SmoothCube/Cube.bam"
        self.sceneSource = "Demoscene.ignore/Sphere/Scene.bam"

        # Load scene from disk
        self.scene = render.attachNewNode("Scene")
        self.debug("Loading Scene '" + self.sceneSource + "'")

        self.model = self.scene.attachNewNode("model")

        for metallic in xrange(2):
            for roughness in xrange(10):
                for specular in xrange(10):

                    model = self.loader.loadModel(self.sceneSource)
                    model.reparentTo(self.model)
                    model.setZ(5.0)
                    model.setX(metallic * 40.0 + roughness*3.0)
                    model.setY(specular*3.0)

                    model.setShaderInput("opt_roughness", roughness / 10.0)
                    model.setShaderInput("opt_metallic", metallic)
                    model.setShaderInput("opt_specular", specular / 10.0)

        ntex = loader.loadTexture("DemoNormalTex.png")
        ntex.setWrapU(Texture.WMRepeat)
        ntex.setWrapV(Texture.WMRepeat)
        ntex.setMinfilter(Texture.FTLinear)
        ntex.setMagfilter(Texture.FTLinear)
        self.model.setShaderInput("demoBumpTex", ntex)


        # Create some lights
        for i in xrange(10):
            continue
            pointLight = PointLight()
            xoffs = (i-25) * 15.0
            pointLight.setPos(xoffs, 0, 8)
            pointLight.setColor(Vec3(random(), random(), random())*1)
            pointLight.setRadius(15)
            self.renderPipeline.addLight(pointLight)

        # Wheter to use a ground floor
        self.usePlane = True
        self.sceneWireframe = False

        # Flatten scene
        self.scene.flattenStrong()

        # Load ground plane if configured
        if self.usePlane:
            self.groundPlane = self.loader.loadModel(
                "Models/Plane/Plane.bam")
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


        # Create a sun light
        dPos = Vec3(60, 30, 100)
        dirLight = DirectionalLight()
        dirLight.setShadowMapResolution(1024)
        dirLight.setPos(dPos)
        dirLight.setColor(Vec3(1))
        dirLight.setPssmTarget(base.cam, base.camLens)
        dirLight.setPssmDistance(180.0)
        dirLight.setCastsShadows(True)

        self.renderPipeline.addLight(dirLight)
        self.dirLight = dirLight
        sunPos = Vec3(56.7587, -31.3601, 189.196)
        self.dirLight.setPos(sunPos)

        self.renderPipeline.setScatteringSource(dirLight)


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

        self.renderPipeline.setEffect(self.model, "DynamicMaterial.effect")

        self.renderPipeline.onSceneInitialized()
        self.renderPipeline.fillTextureStages(render)

        self.createGUI()

    def createGUI(self):
        self.slider_opts = {

            # "roughness": {
            #     "name": "Roughness",
            #     "min": 0.0001,
            #     "max": 1.0,
            #     "default": 0.4,
            # },
            # "metallic": {
            #     "name": "Metallic",
            #     "min": 0.0001,
            #     "max": 1.0,
            #     "default": 0.0,
            # },
            # "specular": {
            #     "name": "Specular",
            #     "min": 0.0001,
            #     "max": 1.0,
            #     "default": 0.5,
            # },
            "bump_factor": {
                "name": "Bump Factor",
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

        self.sliderOrder = ["basecolor_r", "basecolor_g", "basecolor_b", "bump_factor"]


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

        # self.guiParent.getNode().hide()

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
                math.sin(rawValue) * 100.0, math.cos(rawValue) * 100.0, 200)
            # dPos = Vec3(100, 100, (rawValue - 50) * 10.0)
        else:
            dPos = Vec3(30, (rawValue - 50) * 1.5, 100)

        if abs(diff) > 0.0001:
            self.dirLight.setPos(dPos * 10000000.0)

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
