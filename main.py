
import math

from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFile, Vec3, TransparencyAttrib, TextNode

from direct.gui.DirectGui import DirectSlider
from direct.gui.OnscreenText import OnscreenText

from Shared.MovementController import MovementController
from classes.RenderingPipeline import RenderingPipeline
from classes.PointLight import PointLight
from classes.DirectionalLight import DirectionalLight
from classes.BetterShader import BetterShader
from classes.DebugObject import DebugObject

# Redirect output?
# import sys
# sys.stdout = open('Log/log.txt', 'w')
# sys.stderr = open('Log/error.txt', 'w')


class Main(ShowBase, DebugObject):

    def __init__(self):
        DebugObject.__init__(self, "Main")

        # Load engine configuration
        self.debug("Loading panda3d configuration from configuration.prc ..")
        loadPrcFile("configuration.prc")


        self.debug("Creating showbase ..")
        ShowBase.__init__(self)

        self.sceneSource = "Scene/Scene4.egg"
        self.usePlane = False


        self.debug("Loading Scene '" + self.sceneSource + "' ..")
        self.scene = loader.loadModel(self.sceneSource)

        # Load ground plane if configured
        if self.usePlane:
            self.groundPlane = loader.loadModel("Scene/Plane.egg")
            self.groundPlane.setPos(0,0,0)
            self.groundPlane.reparentTo(self.scene)

        # Some artists really don't know about backface culling -.-
        # self.scene.setTwoSided(True)

        self.debug("Flattening scene and parenting to render")
        # self.scene.flattenStrong()
        self.scene.reparentTo(render)

        # Create movement controller
        self.debug("Init movement controller ..")
        self.mc = MovementController(self)
        self.mc.setInitialPosition(Vec3(-40, 40, 40), Vec3(0,0,0))
        self.mc.setup()

        # Hotkey to reload all shaders
        self.accept("r", self.setShaders)
        self.addTask(self.update, "update")

        self.camLens.setNearFar(0.1, 10000)

        self.debug("Creating rendering pipeline ..")

        # Thats really everything you need! Just one line ..
        self.renderPipeline = RenderingPipeline(self)

        # Now let's add some lights
        self.lights = []

        # Store initial light positions for per-frame animations
        self.initialLightPos = []

        colors= [
            Vec3(1,0,0),
            Vec3(0,1,0),
            Vec3(0,0,1),
            Vec3(1,1,0),

            Vec3(1,0,1),
            Vec3(0,1,1),
            Vec3(1,0.5,0),
            Vec3(0,0.5,1.0),

        ]


        if True:
            for i in xrange(8):

                angle = float(i) / 8.0 * math.pi * 2.0

                pos = Vec3(math.sin(angle)*20.0,math.cos(angle)*20.0,9)

                sunLight= PointLight() 
                sunLight.setRadius(35.0)
                sunLight.setColor(colors[i])
                # sunLight.setColor(Vec3(1))
                sunLight.setPos(pos)
                sunLight.setCastsShadows(True)

                if self.renderPipeline:
                    self.renderPipeline.getLightManager().addLight(sunLight)
                self.lights.append(sunLight)
                self.initialLightPos.append(pos)

        if False:
            i = 0
            for x in xrange(3):
                for y in xrange(3):
                    # y = 0.0
                    i += 1
                    if i > 8:
                        continue
                    angle = float(i) / 9.0 * math.pi * 2.0
                    sampleLight = PointLight()
                    sampleLight.setRadius(10.0)

                    # if i < 8:
                    sampleLight.setCastsShadows(True)

                    sampleLight.setColor(Vec3(math.sin(angle)*0.5 + 0.5, math.cos(angle)*0.5+0.5, 0.5) * 1.0)

                    # sampleLight.setColor(Vec3(1))


                    # initialPos = Vec3((x-3.5) * 8.0, (y-3.5)*8.0, 4)
                    initialPos = Vec3(( float(x)-1.5) * 20.0, (float(y)-1.5)* 20.0, 5.0)

                    # initialPos = Vec3(0,0,1)
                    # initialPos = Vec3(0,0,10)

                    sampleLight.setPos(initialPos )

                    self.initialLightPos.append(initialPos)

                    # sampleLight.setPos(Vec3(10, 10, 10))
                    # sampleLight.setHpr(Vec3(180, 0, 0))

                    # sampleLight.attachDebugNode(self.renderDebugNode)

                    if self.renderPipeline:
                        self.renderPipeline.getLightManager().addLight(sampleLight)
                    self.lights.append(sampleLight)



        # create skybox

        self.loadSkybox()

        # self.renderDebugNode.flattenStrong()

        # coord = loader.loadModel("zup-axis")
        # coord.setScale(2.0)
        # coord.reparentTo(self.scene)

        self.setShaders()




    def createMaterialSliders(self):
        OnscreenText(text = 'Specular', pos = (-base.getAspectRatio() + 0.1, 0.85), scale = 0.04, align=TextNode.ALeft, fg=(1,1,1,1))
        OnscreenText(text = 'Metallic', pos = (-base.getAspectRatio() + 0.1, 0.75), scale = 0.04, align=TextNode.ALeft, fg=(1,1,1,1))
        OnscreenText(text = 'Roughness', pos = (-base.getAspectRatio() + 0.1, 0.65), scale = 0.04, align=TextNode.ALeft, fg=(1,1,1,1))

        self.specSlider = DirectSlider(range=(0,100), value=50, pageSize=3, command=self.setSpecular, scale=(0.6,0.5,0.2), pos=(-base.getAspectRatio() + 0.7,0,0.82) )
        self.metSlider = DirectSlider(range=(0,100), value=50, pageSize=3, command=self.setMetallic, scale=(0.6,0.5,0.2), pos=(-base.getAspectRatio() + 0.7,0,0.72) )
        self.roughSlider = DirectSlider(range=(0,100), value=50, pageSize=3, command=self.setRoughness, scale=(0.6,0.5,0.2), pos=(-base.getAspectRatio() + 0.7,0,0.62) )
        
        # Set initial values
        self.setSpecular()
        self.setMetallic()
        self.setRoughness()


    def setSpecular(self):
        self.scene.setShaderInput("specular", float(self.specSlider['value']) / 100.0)

    def setMetallic(self):
        self.scene.setShaderInput("metallic", float(self.metSlider['value']) / 100.0)

    def setRoughness(self):
        self.scene.setShaderInput("roughness", float(self.roughSlider['value']) / 100.0)



    def loadSkybox(self):
        self.skybox = loader.loadModel("Skybox/Skybox")
        self.skybox.setScale(1000)
        self.skybox.reparentTo(render)

    def setShaders(self):
        self.debug("Reloading Shaders ..")

        if self.renderPipeline:
            self.scene.setShader(
                self.renderPipeline.getDefaultObjectShader())
            self.renderPipeline.debugReloadShader()
            
        self.skybox.setShader(BetterShader.load("Shader/DefaultObjectShader.vertex", "Shader/Skybox.fragment"))


    def update(self, task):

        ft = globalClock.getFrameTime()*0.3
        # ft = 0
        for i, light in enumerate(self.lights):
            # pass
            # if i % 3 == 0:
            ft2 = float(i)*math.pi*0.5 + ft * 1.0
            initialPos = self.initialLightPos[i]
            initialPos = Vec3(0,0,9)
            # light.setPos(initialPos + Vec3(math.sin(ft2) * 10.0, math.cos(ft2) * 10.0, math.sin(math.cos(ft2 * 1.523) * 1.7 )  ))


        import time
        time.sleep(30.0 / 1000.0)
        return task.cont


app = Main()
app.run()
