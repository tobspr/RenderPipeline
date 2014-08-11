
from panda3d.core import Texture, NodePath, ShaderAttrib, Vec4, Vec3, Mat4
from panda3d.core import LVecBase3i, PTAVecBase4f, PTAMat4, UnalignedLVecBase4f
from panda3d.core import UnalignedLMatrix4f

from Globals import Globals
from DebugObject import DebugObject
from BetterShader import BetterShader
from LightType import LightType
from GUI.BufferViewerGUI import BufferViewerGUI


class GlobalIllumnination(DebugObject):

    """ This class handles the global illumination processing """

    def __init__(self, pipeline):
        DebugObject.__init__(self, "GlobalIllumnination")
        self.pipeline = pipeline

    def setup(self):
        """ Setups everything for the GI to work """
        self.debug("Setup ..")

        self.cascadeSize = 128

        self.sourcesData = PTAVecBase4f.emptyArray(32)
        self.mvpData = PTAMat4.emptyArray(32)
            
        self.vplStorage = Texture("VPLStorage")
        self.vplStorage.setup2dTexture(
            self.cascadeSize * self.cascadeSize, self.cascadeSize,
            Texture.TFloat, Texture.FRgba16)

        self.vplStorageTemp = Texture("VPLStorageTemp")
        self.vplStorageTemp.setup2dTexture(
            self.cascadeSize * self.cascadeSize, self.cascadeSize,
            Texture.TFloat, Texture.FRgba16)

        self.colorStorage = Texture("ColorStorage")
        self.colorStorage.setup2dTexture(
            self.cascadeSize * self.cascadeSize, self.cascadeSize,
            Texture.TFloat, Texture.FRgba16)

        self.colorStorageTemp = Texture("ColorStorageTemp")
        self.colorStorageTemp.setup2dTexture(
            self.cascadeSize * self.cascadeSize, self.cascadeSize,
            Texture.TFloat, Texture.FRgba16)


        BufferViewerGUI.registerTexture("GI-VPLStorage", self.vplStorage)
        BufferViewerGUI.registerTexture("GI-ColorStorage", self.colorStorage)
        # BufferViewerGUI.registerTexture("GI-VPLStorageTemp", self.vplStorageTemp)
        # BufferViewerGUI.registerTexture("GI-ColorStorageTemp", self.colorStorageTemp)

        self.gridStart = Vec3(-90, -40, -10)
        self.gridEnd = Vec3(90, 40, 75)
        self.delay = 0

        self._createCleanShader()
        self._createPopulateShader()
        self._createSpreadLightingShader()

    def _createCleanShader(self):
        shader = BetterShader.loadCompute("Shader/GI/ClearTexture.compute")
        self.clearTextureNode = NodePath("ClearTexture")
        self.clearTextureNode.setShader(shader)

    def _createPopulateShader(self):
        shader = BetterShader.loadCompute("Shader/GI/PopulateVPL.compute")
        self.populateVPLNode = NodePath("PopulateVPLs")
        self.populateVPLNode.setShader(shader)

    def _createSpreadLightingShader(self):
        shader = BetterShader.loadCompute("Shader/GI/SpreadLighting.compute")
        self.spreadLightingNode = NodePath("SpreadLighting")
        self.spreadLightingNode.setShader(shader)

    def reloadShader(self):
        self._createCleanShader()
        self._createPopulateShader()
        self._createSpreadLightingShader()

    def setLightSource(self, light):

        if light._getLightType() is not LightType.Directional:
            self.error("GI is only supported for directional lights")
            return

        if not light.hasShadows():
            self.error("The directional light needs to have shadows")
            return

        self.debug("Light source is", light)
        self.source = light

    def process(self):

        # if self.delay > 0:
        #     self.delay -= 1
        #     return

        # self.delay = 1

        # Get handle to the atlas textures
        atlas = self.pipeline.getLightManager().shadowComputeTarget
        atlasDepth = atlas.getDepthTexture()
        atlasColor = atlas.getColorTexture()
        atlasNormal = atlas.getAuxTexture(0)
        atlasSize = atlasDepth.getXSize()

        allLights = self.pipeline.getLightManager().getAllLights()
        casters = []

        for light in allLights:
            if light.hasShadows():
                factor = 0.0
                
                if light._getLightType() == LightType.Directional:
                    factor = 1.0

                for source in light.getShadowSources():
                    casters.append((source, factor))

        for index, packed in enumerate(casters):
            caster, factor = packed 
            relativeSize = float(caster.getResolution()) / atlasSize
            relativePos = caster.getAtlasPos()
            self.sourcesData[index] = UnalignedLVecBase4f(relativePos.x, relativePos.y, 
                                    relativeSize, factor) 
            self.mvpData[index] = UnalignedLMatrix4f(caster.mvp)



        projMat = self.source.shadowSources[0].mvp



        # Clear VPL temp storage first
        self.clearTextureNode.setShaderInput("target", self.vplStorageTemp)
        self.clearTextureNode.setShaderInput("clearValue", Vec4(0, 0, 0, 1))
        self._executeShader(self.clearTextureNode, self.cascadeSize*self.cascadeSize / 16, self.cascadeSize / 16)

        # Now populate with VPLs
        self.populateVPLNode.setShaderInput("atlasDepth", atlasDepth)
        self.populateVPLNode.setShaderInput("atlasColor", atlasColor)
        self.populateVPLNode.setShaderInput("atlasNormal", atlasNormal)
        self.populateVPLNode.setShaderInput("lightDirection", self.source.position)
        self.populateVPLNode.setShaderInput("gridStart", self.gridStart)
        self.populateVPLNode.setShaderInput("gridEnd", self.gridEnd)
        self.populateVPLNode.setShaderInput("gridSize", LVecBase3i(self.cascadeSize))
        
        self.populateVPLNode.setShaderInput("lightCount", len(casters))
        self.populateVPLNode.setShaderInput("lightMVPData", self.mvpData)
        self.populateVPLNode.setShaderInput("lightData", self.sourcesData)


        self.populateVPLNode.setShaderInput("sourceMVP", Mat4(projMat))
        self.populateVPLNode.setShaderInput("target", self.vplStorage)
        self.populateVPLNode.setShaderInput("targetColor", self.colorStorage)

        self._executeShader(self.populateVPLNode, self.cascadeSize/4, self.cascadeSize/4, self.cascadeSize/4)

        self.spreadLightingNode.setShaderInput("gridSize", LVecBase3i(self.cascadeSize))
        
        # Spread lighting
        
        for i in xrange(1):
            self.spreadLightingNode.setShaderInput("source", self.vplStorage)
            self.spreadLightingNode.setShaderInput("sourceColor", self.colorStorage)
            self.spreadLightingNode.setShaderInput("target", self.vplStorageTemp)
            self.spreadLightingNode.setShaderInput("targetColor", self.colorStorageTemp)

            self._executeShader(self.spreadLightingNode, self.cascadeSize/4, self.cascadeSize/4, self.cascadeSize/4)

            # Iteration 2
            self.spreadLightingNode.setShaderInput("source", self.vplStorageTemp)
            self.spreadLightingNode.setShaderInput("sourceColor", self.colorStorageTemp)
            self.spreadLightingNode.setShaderInput("target", self.vplStorage)
            self.spreadLightingNode.setShaderInput("targetColor", self.colorStorage)
            self._executeShader(self.spreadLightingNode, self.cascadeSize/4, self.cascadeSize/4, self.cascadeSize/4)


    def bindTo(self, node):
        node.setShaderInput("GI_gridStart", self.gridStart)
        node.setShaderInput("GI_gridEnd", self.gridEnd)
        node.setShaderInput("GI_grid", self.vplStorage)
        node.setShaderInput("GI_gridColor", self.colorStorageTemp)
        node.setShaderInput("GI_cascadeSize", self.cascadeSize)

    def _executeShader(self, node, threadsX, threadsY, threadsZ=1):
        # Retrieve the underlying ShaderAttrib
        sattr = node.get_attrib(ShaderAttrib)

        # Dispatch the compute shader, right now!
        Globals.base.graphicsEngine.dispatch_compute(
            (threadsX, threadsY, threadsZ), sattr, Globals.base.win.get_gsg())
