
import math

from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFileData, Vec3, Vec4, Texture, Shader, TransparencyAttrib


from Shared.MovementController import MovementController
from classes.RenderingPipeline import RenderingPipeline
from classes.PointLight import PointLight

from classes.RenderTarget import RenderTarget
from classes.RenderTargetType import RenderTargetType

# import sys
# sys.stdout = open('Log/log.txt', 'w')
# sys.stderr = open('Log/error.txt', 'w')


class Main(ShowBase):

    def __init__(self):
        self.loadEngineSettings()

        ShowBase.__init__(self)

        # load demo scene
        print "Loading Scene .."
        # self.scene = loader.loadModel("Scene/Scene.egg")
        # self.scene = loader.loadModel("Scene/SceneBam.bam")
        self.scene = loader.loadModel("environment")
        self.scene.setScale(0.1)

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
                    pass
                    cn = self.scenePrefab.copyTo(self.prefabsParent)
                    # cn.setShaderInput("smoothness", float(i) / 10.0)
                    # cn.setShaderInput("gloss", float(j) / 10.0)
                    cn.setPos( (i-5) * 2.5, (j-5)*2.5, 2)
                    # cn.show()
        else:
            self.prefabsParent = self.scene


        self.scene.flattenStrong()

        render.setAttrib(TransparencyAttrib.make(TransparencyAttrib.MNone), 1000)

        self.mc = MovementController(self)
        self.mc.setInitialPosition(Vec3(30, 30, 30), Vec3(0))
        # self.mc.speed = 5.0
        self.mc.setup()

        self.accept("r", self.setShaders)
        self.addTask(self.update, "update")

        self.camLens.setNearFar(0.1, 10000)

        # cubemap = loader.loadCubeMap("Cubemap/#.png")
        # cubemap.setMinfilter(Texture.FTLinearMipmapLinear)
        # cubemap.setMagfilter(Texture.FTLinearMipmapLinear)
        # cubemap.setFormat(Texture.F_srgb_alpha)
        # self.scene.setShaderInput("cubemap", cubemap)

      
        self.renderPipeline = RenderingPipeline(self)

        # # add some lights
        self.lights = []

        self.renderDebugNode = render.attachNewNode("LightDebug")

        i = 0
        for x in xrange(7):
            for y in xrange(8):
                i += 1
                angle = float(i) / 64.0 * math.pi * 2.0
                sampleLight = PointLight()
                sampleLight.setRadius(15.0)



                sampleLight.setColor(Vec3(math.sin(angle)*0.5 + 0.5, math.cos(angle)*0.5+0.5, 0.5))
                sampleLight.setPos( Vec3((x-3.0) * 15.0, (y-3.5)*15.0, 8))
                # sampleLight.setPos(Vec3(10, 10, 10))
                sampleLight.setHpr(Vec3(180, 0, 0))

                sampleLight.attachDebugNode(self.renderDebugNode)

                self.renderPipeline.getLightManager().addLight(sampleLight)
            self.lights.append(sampleLight)

        # add huge sun light
        sunLight= PointLight()
        sunLight.setRadius(10000.0)
        sunLight.setColor(Vec3(0.5,0.5,0.0))
        sunLight.setPos(Vec3(0,0,100))
        self.renderPipeline.getLightManager().addLight(sunLight)


        # self.renderDebugNode.flattenStrong()

        coord = loader.loadModel("zup-axis")
        coord.setScale(2.0)
        coord.reparentTo(self.scene)


        self.setShaders()


    def setShaders(self):
        print "Reloading Shader .."
        self.scene.setShader(
            self.renderPipeline.getDefaultObjectShader())
        self.renderPipeline.debugReloadShader()

    def loadEngineSettings(self):
        loadPrcFileData("", """
            win-size 1600 928
            framebuffer-multisample #f
            multisample #f
            textures-power-2 none
            gl-force-no-error #t
            


        """.strip())

        # gl-debug #t


    def update(self, task):
        # render.setShaderInput("cameraPosition", self.camera.getPos(render))

        return task.cont


app = Main()
app.run()
