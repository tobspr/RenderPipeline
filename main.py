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
from panda3d.core import *
from panda3d.bullet import *
from panda3d.core import loadPrcFile, Vec3
from panda3d.core import Texture

from Code.MovementController import MovementController
from Code.RenderingPipeline import RenderingPipeline
from Code.PointLight import PointLight
from Code.DirectionalLight import DirectionalLight
from Code.BetterShader import BetterShader
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
        # writeDirectory = "Temp/"

        # Clear write directory when app exits
        # atexit.register(os.remove, writeDirectory)

        # Set a write directory, where the shader cache and so on is stored
        # self.renderPipeline.getMountManager().setWritePath(writeDirectory)
        self.renderPipeline.getMountManager().setBasePath(".")

         ####### END OF RENDER PIPELINE SETUP #######
        # Load some demo sourcew
        # self.sceneSource = "Demoscene.ignore/sponza.egg.bam"
        # self.sceneSource = "Demoscene.ignore/occlusionTest/Model.egg"
        self.sceneSource = "Demoscene.ignore/lost-empire/Model.egg"
        # self.sceneSource = "Models/PSSMTest/Model.egg.bam"
        # self.sceneSource = "Demoscene.ignore/GITest/Model.egg"
        # self.sceneSource = "Demoscene.ignore/PSSMTest/Model.egg.bam"
        # self.sceneSource = "Demoscene.ignore/Room/LivingRoom.egg"
        # self.sceneSource = "Models/CornelBox/Model.egg"
        # self.sceneSource = "Models/HouseSet/Model.egg"
        # self.sceneSource = "Toolkit/Blender Material Library/MaterialLibrary.egg"
        # self.sceneSource = "Demoscene.ignore/Forest/forest2.egg.pz"
        # self.sceneSource = "Demoscene.ignore/Weapon1/Model.egg"
        
        self.renderPipeline.loadSettings("Config/pipeline.ini")

        # Create the pipeline, and enable scattering
        self.renderPipeline.create()
        self.renderPipeline.enableDefaultEarthScattering()

        # Load scene from disk
        self.debug("Loading Scene '" + self.sceneSource + "'")
        self.scene = self.loader.loadModel(self.sceneSource)

        # Wheter to use a ground floor
        self.usePlane = False
        self.sceneWireframe = False

        # Flatten scene?
        self.scene.flattenStrong()
        # self.scene.analyze()

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
        dirLight.setColor(Vec3(5))
        dirLight.setPssmDistance(150)
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

        # Load skyboxn
        self.skybox = None
        self.loadSkybox()

        # Set default object shaders
        self.setShaders(refreshPipeline=False)


        # Show windows
        # for window in base.graphicsEngine.getWindows():
            # print window.getName(), window.getSort()

        self.addTask(self._update, "update")

        self.loadCrane()

    def _update(self, task):
        self.animCrane(globalClock.getFrameTime() * 4.0)
        return task.cont

    def animCrane(self,tasktime):
        #self.craneNodes["base"].setH((tasktime%360)*20)
        #lower hydraulics
        self.craneNodes["element2"].setP(-30+math.cos(tasktime/2.)*44) # -30 +- 44
        self.craneNodes["piston1.1"].lookAt(self.craneNodes["piston1.0"],(0,0,0),(0,1,0))
        self.craneNodes["piston1.0"].lookAt(self.craneNodes["piston1.1"],(0,0,0),(0,1,0))

        #middle hydraulics
        angle = 80 +math.cos(tasktime/1.4)*30 #80+-30
        self.craneNodes["arm2"].setP(angle) 

        self.craneNodes["bar0"].setHpr(0,0,0)
        self.craneNodes["bar0"].setP(angle) 

        self.craneNodes["piston0.1"].lookAt(self.craneNodes["piston0.0"])
        self.craneNodes["piston0.0"].lookAt(self.craneNodes["piston0.1"])

        for x in range(4):
          self.craneNodes["element1"].lookAt(self.craneNodes["dummy0"],(0,0,0),(0,1,0))
          self.craneNodes["bar0"].lookAt(self.craneNodes["dummy1"],(0,0,0),(0,-1,-1))
          
        self.craneNodes["arm1"].setH(0)
        self.craneNodes["arm1"].setR(0)
        self.craneNodes["arm1"].setP(-90)
        for x in range(12):

          self.craneNodes["element0"].lookAt(self.craneNodes["arm1"],(0,-0.14,0.16),(0,1,1))
          self.craneNodes["arm1"].lookAt(self.craneNodes["dummy2"],(0,0,0),(0,1,0))
          self.craneNodes["arm1"].setP(self.craneNodes["arm1"].getP()-90-30)
          self.craneNodes["arm1"].setH(0)
          self.craneNodes["arm1"].setR(0)
          
        self.craneNodes["arm0"].setY( 0.1+(1+math.cos(tasktime/3.))*0.5*2  )
        self.cranetip.setTransformDirty()
        self.cardian1bullet.setTransformDirty()
        self.craneNodes["fork"].setH(math.cos(tasktime*1.2)*180)

    def loadCrane(self):
        """ Test script from ThomasEgi """

        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, -9.81))

        self.crane = loader.loadModel("Demoscene.ignore/Forest/crane")
        self.crane.reparentTo(self.scene)


        self.crane.setZ(2.0)
        self.crane.setX(5.0)
        self.crane.setY(1.0)
        self.crane.setH(180)

        self.craneNodes = {}
        for x in ["base","element2","element1","element0","piston1.0","piston1.1","piston0.0","piston0.1","bar0","dummy2","dummy1","dummy0","arm2","arm1","arm0","cardian1","cardian0","fork"]:
            self.craneNodes[x] = self.crane.find("**/"+x)

        #set up physics nao!
        #the tip we'r moving by hand
        self.cranetip = BulletRigidBodyNode('crane-tip')
        self.cranetipNP = self.craneNodes["arm0"].attachNewNode(self.cranetip)
        #self.cranetipNP.node().addShape(shape)
        self.cranetipNP.setCollideMask(BitMask32.allOn())
        self.cranetipNP.setPos( self.craneNodes["cardian1"].getPos())
        self.world.attachRigidBody(self.cranetip)

        #the stuff dangling around...
        shape = BulletBoxShape(Vec3(0.3, 0.35, 0.5))
        cardian1Bulletbody = BulletRigidBodyNode('cardian1bulletBodyNode')
        cardian1Bulletbody.setAngularDamping(0.7)
        cardian1BulletNP = self.craneNodes["arm0"].attachNewNode(cardian1Bulletbody)
        cardian1BulletNP.node().addShape(shape)
        cardian1BulletNP.node().setMass(1.0)
        cardian1BulletNP.setCollideMask(BitMask32.allOn())
        cardian1BulletNP.setPos( self.craneNodes["cardian1"].getPos()-(0,0,1.4) )
        self.craneNodes["cardian1"].wrtReparentTo(cardian1BulletNP)
        self.cardian1bullet = cardian1Bulletbody
        self.world.attachRigidBody(cardian1Bulletbody)
        #self.craneNodes["cardian1"].node().addshape(shape)


        pivotA = Point3(0,0,0) #self.craneNodes["cardian1"].getPos(self.craneNodes["arm0"])
        pivotB = Point3(0, 0,1.4)
        axisA = Vec3(1, 0, 0)
        axisB = Vec3(1, 0, 0)

        hinge = BulletHingeConstraint(self.cranetip, cardian1Bulletbody, pivotA, pivotB, axisA, axisB, True)
        hinge.setDebugDrawSize(2.0)
        hinge.setLimit(-70, 179, softness=0.9, bias=0.3, relaxation=1.0)
        self.world.attachConstraint(hinge)
           


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

    def loadSkybox(self):
        """ Loads the skybox """
        self.skybox = self.loader.loadModel("Models/Skybox/Model.egg.bam")
        self.skybox.setScale(40000)
        self.skybox.reparentTo(self.render)
        skytex = loader.loadTexture("Data/Skybox/sky.jpg")
        # skytex.setFormat(Texture.FSrgb)
        # skytex.setMinfilter(Texture.FTLinear)
        # skytex.setMagfilter(Texture.FTLinear)
        self.skybox.setShaderInput("skytex", skytex)

    def setShaders(self, refreshPipeline=True):
        """ Sets all shaders """
        self.debug("Reloading Shaders ..")

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
        to use it with tesselation shaders """
        self.debug("Converting model to patches ..")
        for node in model.find_all_matches("**/+GeomNode"):
            geom_node = node.node()
            num_geoms = geom_node.get_num_geoms()
            for i in range(num_geoms):
                geom_node.modify_geom(i).make_patches_in_place()

app = Main()
app.run()
