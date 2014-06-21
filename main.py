
import math

from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFileData, Vec3, Vec4, Texture, Shader


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
        self.scene = loader.loadModel("Scene/SceneBam.bam")
        # self.scene = loader.loadModel("Scene/Scene2Bam.bam")

        # self.scene = loader.loadModel("panda")
        self.scene.reparentTo(render)

        # place prefabs
        # self.scenePrefab = self.scene.find("Prefab")
        # self.scenePrefab.hide()
        # self.prefabsParent = self.scene.attachNewNode("Prefabs")
        # for i in xrange(11):
        #     for j in xrange(11):
        #         cn = self.scenePrefab.copyTo(self.prefabsParent)
        #         cn.setShaderInput("smoothness", float(i) / 10.0)
        #         cn.setShaderInput("gloss", float(j) / 10.0)
        #         cn.setPos( (i-5) * 2.5, (j-5)*2.5, 1.1)
        #         cn.show()
        self.prefabsParent = self.scene
        self.scene.flattenStrong()

        self.mc = MovementController(self)
        self.mc.setInitialPosition(Vec3(10, 10, 10), Vec3(0))
        self.mc.setup()

        self.accept("r", self.setShaders)
        self.addTask(self.update, "update")

        self.camLens.setNearFar(0.1, 1000)

        cubemap = loader.loadCubeMap("Cubemap/#.png")
        cubemap.setMinfilter(Texture.FTLinearMipmapLinear)
        cubemap.setMagfilter(Texture.FTLinearMipmapLinear)
        # cubemap.setFormat(Texture.F_srgb_alpha)
        cubemap.setFormat(Texture.F_srgb_alpha)
        self.scene.setShaderInput("cubemap", cubemap)

        # base.win.setClearColorActive(True)
        # base.win.setClearColor(Vec4(0.5, 0.5, 0.5, 1.0))

        self.renderPipeline = RenderingPipeline(self)

        # add some lightz
        self.lightz = []

        self.renderDebugNode = render.attachNewNode("LightDebug")

        for i in xrange(256):
            angle = float(i) / 256.0 * math.pi * 2.0
            sampleLight = HemiPointLight()
            sampleLight.setRadius(5.0)
            sampleLight.setColor(Vec3(1.0, 0.5, 0.2))
            sampleLight.setPos(Vec3(math.sin(angle)*80.0, math.cos(angle)*80.0, 5))
            sampleLight.setHpr(Vec3(180, 0, 0))

            # sampleLight.attachDebugNode(self.renderDebugNode)

            self.renderPipeline.getLightManager().addLight(sampleLight)
            self.lightz.append(sampleLight)

        self.renderDebugNode.flattenStrong()

        coord = loader.loadModel("zup-axis")
        coord.setScale(2.0)
        coord.reparentTo(render)

        # rb = RenderTarget("Test")

        # rb.addRenderTexture(RenderTargetType.Color)
        # rb.addRenderTexture(RenderTargetType.Depth)
        # rb.addRenderTexture(RenderTargetType.Aux0)
        # rb.addRenderTexture(RenderTargetType.Aux1)
        # rb.addRenderTexture(RenderTargetType.Aux2)
        # rb.prepareSceneRender()

        # self.rb = rb


        # rb.getQuad().setShaderInput("color", rb.getTexture(RenderTargetType.Color))
        # rb.getQuad().setShaderInput("aux0", rb.getTexture(RenderTargetType.Aux0))
        # rb.getQuad().setShaderInput("aux1", rb.getTexture(RenderTargetType.Aux1))
        # rb.getQuad().setShaderInput("depth",
        # rb.getTexture(RenderTargetType.Depth))

        self.setShaders()


        

    def setShaders(self):
        print "Reloading Shader .."
        self.prefabsParent.setShader(
            self.renderPipeline.getDefaultObjectShader())
        # fsb = Shader.load(Shader.SLGLSL, "Shader/DefaultPostProcess.vertex", "Shader/FullScreenBlur.fragment")
        # self.rb.getQuad().setShader(fsb)




    def loadEngineSettings(self):
        loadPrcFileData("", """
            win-size 1600 900
            framebuffer-multisample #f
            multisample #f

            textures-power-2 none
            

        """.strip())

    def update(self, task):
        render.setShaderInput("cameraPosition", self.camera.getPos(render))

        radius = 30.0 + math.sin(globalClock.getFrameTime())*14.0
        # for light in self.lightz:

        #     light.setRadius(radius)

        return task.cont


app = Main()
app.run()
