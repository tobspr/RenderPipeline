
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

# import sys
# sys.stdout = open('Log/log.txt', 'w')
# sys.stderr = open('Log/error.txt', 'w')


class Main(ShowBase):

    def __init__(self):
        self.loadEngineSettings()

        ShowBase.__init__(self)

        # load demo scene
        print "Loading Scene .."
        self.scene = loader.loadModel("Scene/Scene1.egg")
        # self.scene = loader.loadModel("Scene/Scene2.egg")

        # self.groundPlane = loader.loadModel("Scene/Plane.egg")
        # self.groundPlane.reparentTo(self.scene)
        # self.groundPlane.setPos(0,0,-3)

        # self.scene = loader.loadModel("Scene.ignore/Car.bam")
        
        # panda = loader.loadModel("panda")
        # panda.reparentTo(self.scene)
        # panda.setPos(10,0,0.5)
        # panda.setH(180)
        # panda.setScale(0.5)
        # self.scene.setScale(2.0)

        # self.scene.setTwoSided(True)
        # self.scene = loader.loadModel("Scene/Scene2Bam.bam")
# 
        # self.scene.flattenStrong()
        # self.scene = loader.loadModel("environment")
        # self.scene.setScale(0.1)

        # self.scene = loader.loadModel("panda")
        self.scene.reparentTo(render)

        if False:
            print "Placing prefabs"
            # place prefabs
            self.scenePrefab = self.scene.find("Prefab")
            # self.scenePrefab.flattenStrong()
            # self.scenePrefab.hide()
            self.prefabsParent = self.scene.attachNewNode("Prefabs")
            for i in xrange(10):
                for j in xrange(10):
                    # pass
                    cn = self.scenePrefab.copyTo(self.prefabsParent)
                    # cn.setShaderInput("smoothness", float(i) / 10.0)
                    # cn.setShaderInput("gloss", float(j) / 10.0)
                    cn.setPos( (i-5) * 2.5, (j-5)*2.5, 5)
                    # cn.show()
        else:
            self.prefabsParent = self.scene


        # self.scene.flattenStrong()

        render.setAttrib(TransparencyAttrib.make(TransparencyAttrib.MNone), 1000)

        self.mc = MovementController(self)
        self.mc.setInitialPosition(Vec3(-70, 70, 70), Vec3(0,0,0))
        # self.mc.speed = 5.0
        self.mc.setup()

        self.accept("r", self.setShaders)
        self.addTask(self.update, "update")

        self.camLens.setNearFar(1.0, 10000)
        self.renderPipeline = RenderingPipeline(self)

        # add some lights
        self.lights = []

        self.renderDebugNode = render.attachNewNode("LightDebug")
        
        # add huge sun light

        # for i in xrange(1):
        #     sunLight = DirectionalLight()
        #     sunLight.setColor(Vec3(0.1))
        #     angle = float(i) / 20.0 * math.pi * 2.0
        #     sunLight.setDirection(Vec3(math.sin(angle),math.cos(angle),1))
        #     # sunLight.setCastsShadows(True)
        #     self.renderPipeline.getLightManager().addLight(sunLight)
        #     self.lights.append(sunLight)

        # inverseSunLight = DirectionalLight()
        # inverseSunLight.setColor(Vec3(0.5))
        # inverseSunLight.setPos(Vec3(-10,10,15))
        # inverseSunLight.setDirection(Vec3(-1000,500,1000))
        # # sunLight.setCastsShadows(True)
        # self.renderPipeline.getLightManager().addLight(inverseSunLight)
        # self.lights.append(inverseSunLight)


        sunLight2= PointLight()
        sunLight2.setRadius(35.0)
        sunLight2.setColor(Vec3(1.0))
        sunLight2.setPos(Vec3(5,5,15))
        sunLight2.setCastsShadows(True)
        self.renderPipeline.getLightManager().addLight(sunLight2)
        # sunLight.attachDebugNode(self.renderDebugNode)

        self.lights.append(sunLight2)

        # self.initialLightPos = [Vec3(5,5,9), Vec3(-5,-5,7)]
        # self.initialLightPos = [Vec3(5,5,9)]
        # self.initialLightPos = [Vec3(0)]
        self.initialLightPos = []

        if False:
            i = 0
            for x in xrange(4):
                for y in xrange(3):
                    # y = 0.0
                    i += 1
                    if i > 34:
                        continue
                    angle = float(i) / 9.0 * math.pi * 2.0
                    sampleLight = PointLight()
                    sampleLight.setRadius(30.0)

                    # if i < 8:
                    sampleLight.setCastsShadows(True)

                    sampleLight.setColor(Vec3(math.sin(angle)*0.5 + 0.5, math.cos(angle)*0.5+0.5, 0.5) * 1.0)

                    # sampleLight.setColor(Vec3(1))


                    # initialPos = Vec3((x-3.5) * 8.0, (y-3.5)*8.0, 4)
                    initialPos = Vec3(( float(x)-1.5) * 5.0, (float(y)-1.5)* 5.0, 12.0)
                    # initialPos = Vec3(0,0,10)

                    sampleLight.setPos(initialPos )

                    self.initialLightPos.append(initialPos)

                    # sampleLight.setPos(Vec3(10, 10, 10))
                    # sampleLight.setHpr(Vec3(180, 0, 0))

                    # sampleLight.attachDebugNode(self.renderDebugNode)

                    self.renderPipeline.getLightManager().addLight(sampleLight)
                    self.lights.append(sampleLight)



        # create skybox

        self.loadSkybox()

        # self.renderDebugNode.flattenStrong()

        # coord = loader.loadModel("zup-axis")
        # coord.setScale(2.0)
        # coord.reparentTo(self.scene)

        self.setShaders()



        # OnscreenText(text = 'Specular', pos = (-base.getAspectRatio() + 0.1, 0.85), scale = 0.04, align=TextNode.ALeft, fg=(1,1,1,1))
        # OnscreenText(text = 'Metallic', pos = (-base.getAspectRatio() + 0.1, 0.75), scale = 0.04, align=TextNode.ALeft, fg=(1,1,1,1))
        # OnscreenText(text = 'Roughness', pos = (-base.getAspectRatio() + 0.1, 0.65), scale = 0.04, align=TextNode.ALeft, fg=(1,1,1,1))

        # self.specSlider = DirectSlider(range=(0,100), value=50, pageSize=3, command=self.setSpecular, scale=(0.6,0.5,0.2), pos=(-base.getAspectRatio() + 0.7,0,0.82) )
        # self.metSlider = DirectSlider(range=(0,100), value=50, pageSize=3, command=self.setMetallic, scale=(0.6,0.5,0.2), pos=(-base.getAspectRatio() + 0.7,0,0.72) )
        #     # self.roughSlider = DirectSlider(range=(0,100), value=50, pageSize=3, command=self.setRoughness, scale=(0.6,0.5,0.2), pos=(-base.getAspectRatio() + 0.7,0,0.62) )
        #     self.setSpecular()
        #     self.setMetallic()
        #     self.setRoughness()
         
        # def setSpecular(self):
        #     self.scene.setShaderInput("specular", float(self.specSlider['value']) / 100.0)

        # def setMetallic(self):
        #     self.scene.setShaderInput("metallic", float(self.metSlider['value']) / 100.0)

        # def setRoughness(self):
        #     self.scene.setShaderInput("roughness", float(self.roughSlider['value']) / 100.0)





    def loadSkybox(self):
        self.skybox = loader.loadModel("Skybox/Skybox")
        self.skybox.setScale(1000)
        self.skybox.reparentTo(render)

    def setShaders(self):
        print "Reloading Shader .."
        self.scene.setShader(
            self.renderPipeline.getDefaultObjectShader())
        self.renderPipeline.debugReloadShader()
        
        self.skybox.setShader(BetterShader.load("Shader/DefaultObjectShader.vertex", "Shader/Skybox.fragment"))

    def loadEngineSettings(self):
        loadPrcFile("configuration.prc")
        # pass

    def update(self, task):

        ft = globalClock.getFrameTime()*1.0
        # ft = 0
        for i, light in enumerate(self.lights):
            ft += float(i) + math.pi*0.46
            # initialPos = self.initialLightPos[i]
            # light.setPos(initialPos + Vec3(math.sin(ft) * 3.0, math.cos(ft) * 3.0, math.sin(math.cos(ft * 1.523) * 1.7 )  ))
        return task.cont


app = Main()
app.run()
