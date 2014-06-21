
import math
from panda3d.core import Shader, TransparencyAttrib, Texture, Vec2, ComputeNode

from LightManager import LightManager
from RenderTarget import RenderTarget
from RenderTargetType import RenderTargetType
from DebugObject import DebugObject



class RenderingPipeline(DebugObject):

    def __init__(self, showbase):
        DebugObject.__init__(self, "RenderingPipeline")
        self.showbase = showbase
        self.lightManager = LightManager()
        self.size = self._getSize()
        self.camera = base.cam
        self.cullBounds = None
        self._setup()

    def _setup(self):
        self.debug("Setting up render pipeline")

        # First, we need no transparency
        render.setAttrib(
            TransparencyAttrib.make(TransparencyAttrib.MNone), 100)

        # Now create deferred render buffers
        self._makeDeferredTargets()

        # Setup compute shader for lighting
        self._createLightingPipeline()


        # for debugging attach texture to shader
        self.deferredTarget.getQuad().setShader(Shader.load(Shader.SLGLSL, "Shader/DefaultPostProcess.vertex", "Shader/TextureDisplay.fragment"))
        self.deferredTarget.getQuad().setShaderInput("sampler", self.lightingPassTex)
        # self.deferredTarget.getQuad().setShaderInput("sampler", self.deferredTarget.getTexture(RenderTargetType.Aux1))

        # add update task
        self._attachUpdateTask()


    def _makeDeferredTargets(self):
        self.debug("Creating deferred targets")
        self.deferredTarget = RenderTarget("DeferredTarget")
        self.deferredTarget.addRenderTexture(RenderTargetType.Color)
        self.deferredTarget.addRenderTexture(RenderTargetType.Depth)
        self.deferredTarget.addRenderTexture(RenderTargetType.Aux0)
        self.deferredTarget.addRenderTexture(RenderTargetType.Aux1)
        self.deferredTarget.setAuxBits(16)
        self.deferredTarget.setColorBits(16)
        self.deferredTarget.prepareSceneRender()

    def _createLightingPipeline(self):
        self.debug("Creating lighting compute shader")

        # size has to be a multiple of the compute unit size
        sizeX = int(math.ceil(self.size.x / 32))
        sizeY = int(math.ceil(self.size.y / 32))

        # create a texture where the shader can write to
        self.lightingPassTex = Texture("LightingPassResult")
        self.lightingPassTex.setup_2d_texture(sizeX*32,sizeY*32, Texture.TFloat, Texture.FRgba8)
        self.lightingPassTex.setMinfilter(Texture.FTNearest)
        self.lightingPassTex.setMagfilter(Texture.FTNearest)
        # self.lightingPassTex.clearRamImage() # doesn't work

        # create compute node
        self.lightingComputeNode = ComputeNode("LightingComputePass")
        self.lightingComputeNode.add_dispatch(sizeX, sizeY, 1)

        # attach compute node to scene graph
        self.lightingComputeContainer = render.attachNewNode(self.lightingComputeNode)
        self.lightingComputeContainer.setShader(self.lightManager.getPipelineShader())
        self.lightingComputeContainer.setShaderInput("destination", self.lightingPassTex)
        self.lightingComputeContainer.setShaderInput("target0", self.deferredTarget.getTexture(RenderTargetType.Aux0))
        # self.lightingComputeContainer.setShaderInput("target1", self.deferredTarget.getTexture(RenderTargetType.Aux0))
        # self.lightingComputeContainer.setShaderInput("target2", self.deferredTarget.getTexture(RenderTargetType.Aux1))
        self.lightingComputeContainer.setBin("unsorted", 10)
        # self.lightingPassTex.setup_2d_texture(
            # int(self.size.x), int(self.size.y), Texture.TFloat, Texture.FRgba16)

    def _getSize(self):
        return Vec2(
            int(self.showbase.win.getXSize()),
            int(self.showbase.win.getYSize()))

    def _attachUpdateTask(self):
        self.showbase.addTask(self._update, "UpdateRenderingPipeline")

    def _computeCameraBounds(self):
        # compute camera bounds in render space
        cameraBounds = self.camera.node().getLens().makeBounds()
        cameraBounds.xform(self.camera.getMat(render))
        return cameraBounds

    def _update(self, task):
        self.cullBounds = self._computeCameraBounds()

        self.lightManager.setCullBounds(self.cullBounds)
        self.lightManager.update()

        return task.cont

    def getLightManager(self):
        return self.lightManager

    def getDefaultObjectShader(self):
        shader = Shader.load(
            Shader.SLGLSL, "Shader/DefaultObjectShader.vertex", "Shader/DefaultObjectShader.fragment")
        return shader
