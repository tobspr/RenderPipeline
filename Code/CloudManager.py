


from panda3d.core import Texture, Shader, ShaderAttrib, NodePath
from DebugObject import DebugObject
from MemoryMonitor import MemoryMonitor
from .Globals import Globals
from RenderPasses.CloudRenderPass import CloudRenderPass

class CloudManager(DebugObject):


    def __init__(self, pipeline):
        """ Creates the manager """
        DebugObject.__init__(self, "CloudManager")
        self.pipeline = pipeline#
        self.create()

    def create(self):
        """ Creates the passes """
        self.cloudStartHeight = 900.0
        self.cloudEndHeight = 3300.0
        self.cloudResolution = 768
        self.cloudResolutionH = 128

        self.voxelGrid = Texture("CloudVoxelGrid")
        self.voxelGrid.setup3dTexture(self.cloudResolution, self.cloudResolution, self.cloudResolutionH, Texture.TFloat, Texture.FR16)
        self.voxelGrid.setWrapU(Texture.WMRepeat)
        self.voxelGrid.setWrapV(Texture.WMRepeat)
        self.voxelGrid.setWrapW(Texture.WMClamp)

        self.cloudNoise = Texture("CloudNoise")
        self.cloudNoise.setup3dTexture(64, 64, 64, Texture.TFloat, Texture.FR16)
        self.cloudNoise.setWrapU(Texture.WMRepeat)
        self.cloudNoise.setWrapV(Texture.WMRepeat)
        self.cloudNoise.setWrapW(Texture.WMRepeat)

        MemoryMonitor.addTexture("CloudVoxelGrid", self.voxelGrid)
        MemoryMonitor.addTexture("CloudNoise", self.cloudNoise)

        self._createInitialGrid()

        self.renderPass = CloudRenderPass()
        self.pipeline.getRenderPassManager().registerPass(self.renderPass)
        self.pipeline.getRenderPassManager().registerStaticVariable("cloudVoxelGrid", self.voxelGrid)
        self.pipeline.getRenderPassManager().registerStaticVariable("cloudStartHeight", self.cloudStartHeight)
        self.pipeline.getRenderPassManager().registerStaticVariable("cloudEndHeight", self.cloudEndHeight)
        self.pipeline.getRenderPassManager().registerStaticVariable("cloudNoise", self.cloudNoise)
        self.pipeline.getRenderPassManager().registerDefine("CLOUDS_ENABLED", 1)


    def update(self):
        """ Updates the clouds """


    def _createInitialGrid(self):
        """ Creates the initial cloud grid """
        shader = Shader.loadCompute(Shader.SLGLSL, "Shader/Clouds/InitialGrid.compute")
        dummy = NodePath("dummy")
        dummy.setShader(shader)
        dummy.setShaderInput("cloudGrid", self.voxelGrid)
        sattr = dummy.getAttrib(ShaderAttrib)
        Globals.base.graphicsEngine.dispatch_compute(
            (self.cloudResolution / 8, self.cloudResolution / 8, self.cloudResolutionH / 8), sattr, Globals.base.win.getGsg())

        shader = Shader.loadCompute(Shader.SLGLSL, "Shader/Clouds/CloudNoise.compute")
        dummy = NodePath("dummy")
        dummy.setShader(shader)
        dummy.setShaderInput("noiseGrid", self.cloudNoise)
        sattr = dummy.getAttrib(ShaderAttrib)
        Globals.base.graphicsEngine.dispatch_compute(
            (64 / 8, 64 / 8, 64 / 8), sattr, Globals.base.win.getGsg())
