
import math

from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFileData, Vec3, Vec4, Texture, Shader, TransparencyAttrib


from MovementController import MovementController
from classes.RenderingPipeline import RenderingPipeline
from classes.HemiPointLight import HemiPointLight

from classes.RenderTarget import RenderTarget
from classes.RenderTargetType import RenderTargetType


class Main(ShowBase):

    def __init__(self):
        self.loadEngineSettings()

        ShowBase.__init__(self)

        # load demo scene
        print "Loading Scene .."
        self.scene = loader.loadModel("Scene/Scene.egg")

        # self.scene = loader.loadModel("panda")
        self.scene.reparentTo(render)

        if True:
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
                    cn.setPos( (i-5) * 2.5, (j-5)*2.5, 5)
                    # cn.show()
        else:
            self.prefabsParent = self.scene


        self.scene.flattenStrong()

        render.setAttrib(TransparencyAttrib.make(TransparencyAttrib.MNone), 1000)

        self.mc = MovementController(self)
        self.mc.setInitialPosition(Vec3(10, 10, 10), Vec3(0))
        self.mc.setup()

        self.accept("r", self.setShaders)
        self.addTask(self.update, "update")

        self.camLens.setNearFar(0.1, 1000)

        # cubemap = loader.loadCubeMap("Cubemap/#.png")
        # cubemap.setMinfilter(Texture.FTLinearMipmapLinear)
        # cubemap.setMagfilter(Texture.FTLinearMipmapLinear)
        # cubemap.setFormat(Texture.F_srgb_alpha)
        # self.scene.setShaderInput("cubemap", cubemap)

      
        self.renderPipeline = RenderingPipeline(self)

        # add some lights
        self.lights = []

        self.renderDebugNode = render.attachNewNode("LightDebug")

        for i in xrange(1):
            angle = float(i) / 128.0 * math.pi * 2.0
            sampleLight = HemiPointLight()
            sampleLight.setRadius(15.0)
            sampleLight.setColor(Vec3(1.0, 0.5, 0.2))
            sampleLight.setPos(Vec3(math.sin(angle)*80.0, math.cos(angle)*80.0, 8))
            sampleLight.setPos(Vec3(10, 10, 10))
            sampleLight.setHpr(Vec3(180, 0, 0))

            sampleLight.attachDebugNode(self.renderDebugNode)

            self.renderPipeline.getLightManager().addLight(sampleLight)
            self.lights.append(sampleLight)

        self.renderDebugNode.flattenStrong()

        coord = loader.loadModel("zup-axis")
        coord.setScale(2.0)
        coord.reparentTo(self.scene)


        self.setShaders()


    def setShaders(self):
        print "Reloading Shader .."
        render.setShader(
            self.renderPipeline.getDefaultObjectShader())

    def loadEngineSettings(self):
        loadPrcFileData("", """
            win-size 1600 900
            framebuffer-multisample #f
            multisample #f
            textures-power-2 none

        """.strip())

    def update(self, task):
        # render.setShaderInput("cameraPosition", self.camera.getPos(render))

        return task.cont


app = Main()
app.run()
