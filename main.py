
import math

from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFileData, Vec3, TransparencyAttrib


from Shared.MovementController import MovementController
from classes.RenderingPipeline import RenderingPipeline
from classes.PointLight import PointLight
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
        self.scene = loader.loadModel("Scene/Scene4.egg")
        # self.scene = loader.loadModel("Scene/SceneBam.bam")
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
        self.mc.setInitialPosition(Vec3(70, 70, 70), Vec3(0,0,0))
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
        sunLight= PointLight()
        sunLight.setRadius(30.0)
        sunLight.setColor(Vec3(0.7, 0.7, 0.7))
        sunLight.setPos(Vec3(2,2,9))
        sunLight.setCastsShadows(True)
        self.renderPipeline.getLightManager().addLight(sunLight)
        # sunLight.attachDebugNode(self.renderDebugNode)

        self.lights.append(sunLight)

        self.initialLightPos = [Vec3(2,2,9)]

        if False:
            i = 0
            for x in xrange(8):
                for y in xrange(7):
                    i += 1
                    if i > 63:
                        continue
                    angle = float(i) / 64.0 * math.pi * 2.0
                    sampleLight = PointLight()
                    sampleLight.setRadius(15.0)

                    sampleLight.setColor(Vec3(math.sin(angle)*0.5 + 0.5, math.cos(angle)*0.5+0.5, 0.5) * 2.0)
                    # sampleLight.setColor(Vec3(2,2,2) * 2.0)


                    # initialPos = Vec3((x-3.5) * 8.0, (y-3.5)*8.0, 4)
                    initialPos = Vec3((x-3.5) * 13.0, (y-3.5)*13.0, 1)
                    # initialPos = Vec3(0,0,10)

                    sampleLight.setPos(initialPos )

                    self.initialLightPos.append(initialPos)

                    # sampleLight.setPos(Vec3(10, 10, 10))
                    sampleLight.setHpr(Vec3(180, 0, 0))

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
        loadPrcFileData("", """
            window-title Render Pipeline
            win-size 1600 960
            win-fixed-size #t
            framebuffer-multisample #f
            multisample #f
            textures-power-2 none
            framebuffer-srgb #f
            
            gl-dump-compiled-shaders #f

            frame-rate-meter-text-pattern %0.2f fps
            frame-rate-meter-ms-text-pattern %0.3f ms
            # frame-rate-meter-side-margins 0.4
            frame-rate-meter-scale 0.04
            text-default-font Font/SourceSansPro-Regular.otf
            frame-rate-meter-milliseconds #t
            sync-video #f

            transform-cache #t
            state-cache #t

            # Gimme all that performance!
            # threading-model App/Cull/Draw
            gl-finish #f
            gl-force-no-error #t
            gl-force-no-flush #t
            gl-force-no-scissor #t

        """.strip())


    def update(self, task):

        ft = globalClock.getFrameTime()
        for i, light in enumerate(self.lights):
            ft += float(i)
            initialPos = self.initialLightPos[i]
            light.setPos(initialPos + Vec3(math.sin(ft) * 5.0, math.cos(ft) * 5.0, math.sin(math.cos(ft * 1.523) * 1.23 )  ))
        return task.cont


app = Main()
app.run()
