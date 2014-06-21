

from panda3d.core import Shader, TransparencyAttrib, Texture, Vec2

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
        # self.deferredTarget.getQuad().setShaderInput("sampler", self.lightingPassTex)
        self.deferredTarget.getQuad().setShaderInput("sampler", self.deferredTarget.getTexture(RenderTargetType.Color))

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

        # first, create a texture where the shader can write to
        self.lightingPassTex = Texture("LightingPassResult")
        # self.lightingPassTex.setup_2d_texture(
            # int(self.size.x), int(self.size.y), Texture.TFloat, Texture.FRgba16)

    def _getSize(self):
        return Vec2(
            int(self.showbase.win.getXSize()),
            int(self.showbase.win.getYSize()))

    def _attachUpdateTask(self):
        self.showbase.addTask(self._update, "UpdateRenderingPipeline")

    def _update(self, task):
        self.lightManager.update()

        return task.cont

    def getLightManager(self):
        return self.lightManager

    def getDefaultObjectShader(self):
        shader = Shader.load(
            Shader.SLGLSL, "Shader/DefaultObjectShader.vertex", "Shader/DefaultObjectShader.fragment")
        return shader
