
from panda3d.core import NodePath, Camera, SamplerState, Shader
from panda3d.core import ColorWriteAttrib

from Code.Globals import Globals
from Code.RenderPass import RenderPass
from Code.RenderTarget import RenderTarget

class ShadowScenePass(RenderPass):

    def __init__(self):
        RenderPass.__init__(self)

        self.maxRegions = 8
        self.shadowScene = Globals.base.render

    def setMaxRegions(self, maxRegions):
        self.maxRegions = maxRegions

    def getID(self):
        return "ShadowScenePass"

    def getRequiredInputs(self):
        return {
            "numUpdates": "Variables.numShadowUpdates",
            "updateSources": "Variables.shadowUpdateSources" 
        }

    def setShaders(self):
        self.createTagStates()

    def setSize(self, size):
        self.size = size

    def setActiveRegionCount(self, activeCount):
        if activeCount < 1:
            self.target.setActive(False)
        else:
            self.target.setActive(True)
            for index, region in enumerate(self.renderRegions):
                if index < activeCount:
                    region.setActive(True)
                else:
                    region.setActive(False)

    def setRegionDimensions(self, index, l, r, b, t):
        self.renderRegions[index].setDimensions(l, r, b, t)

    def getRegionCamera(self, index):
        return self.shadowCameras[index]

    def createTagStates(self):
        casterShader = Shader.load(Shader.SLGLSL,
            "Shader/DefaultShaders/ShadowCasting/vertex.glsl",
            "Shader/DefaultShaders/ShadowCasting/fragment.glsl")
        initialState = NodePath("ShadowCasterState")
        initialState.setShader(casterShader, 100)
        for camera in self.shadowCameras:
            camera.node().setTagState("Default", initialState.getState())

        casterShaderTransparent = Shader.load(Shader.SLGLSL,
            "Shader/DefaultShaders/TransparentShadowCasting/vertex.glsl",
            "Shader/DefaultShaders/TransparentShadowCasting/fragment.glsl")
        initialState = NodePath("ShadowCasterStateTransparent")
        initialState.setShader(casterShaderTransparent, 100)
        for camera in self.shadowCameras:
            camera.node().setTagState("Transparent", initialState.getState()) 

    def create(self):

        # Create the atlas target
        self.target = RenderTarget("ShadowAtlas")
        self.target.setSize(self.size)
        self.target.addDepthTexture()
        self.target.setDepthBits(32)
        self.target.setColorWrite(False)
        self.target.setActive(False)

        self.target.setSource(
            NodePath(Camera("tmp")), Globals.base.win)

        self.target.prepareSceneRender()

        # Set the appropriate filter modes
        dTex = self.target.getDepthTexture()
        dTex.setWrapU(SamplerState.WMClamp)
        dTex.setWrapV(SamplerState.WMClamp)

        # Remove the default postprocess quad
        self.target.getQuad().node().removeAllChildren()
        self.target.getInternalRegion().setSort(-200)
        self.target.getInternalRegion().disableClears()
        self.target.getInternalBuffer().disableClears()
        self.target.getInternalBuffer().setSort(-300)

        # Create default initial state
        initialState = NodePath("InitialState")
        # initialState.setAttrib(ColorWriteAttrib.make(ColorWriteAttrib.COff))

        # Create a camera for each update
        self.shadowCameras = []
        for i in xrange(self.maxRegions):
            shadowCam = Camera("ShadowComputeCamera")
            shadowCam.setTagStateKey("ShadowPassShader")
            shadowCam.setInitialState(initialState.getState())
            shadowCamNode = self.shadowScene.attachNewNode(shadowCam)
            self.shadowCameras.append(shadowCamNode)

        # Create regions
        self.renderRegions = []
        buff = self.target.getInternalBuffer()
        
        for i in xrange(self.maxRegions):
            dr = buff.makeDisplayRegion()
            dr.setSort(1000)
            dr.setClearDepthActive(True)
            dr.setClearDepth(1.0)
            dr.setCamera(self.shadowCameras[i])
            dr.setActive(False)
            self.renderRegions.append(dr)

        self.pcfSampleState = SamplerState()
        self.pcfSampleState.setMinfilter(SamplerState.FTShadow)
        self.pcfSampleState.setMagfilter(SamplerState.FTShadow)
        self.pcfSampleState.setWrapU(SamplerState.WMClamp)
        self.pcfSampleState.setWrapV(SamplerState.WMClamp)

        Globals.render.setTag("ShadowPassShader", "Default")

    def getOutputs(self):
        return {
            "ShadowScenePass.atlas": lambda: self.target.getDepthTexture(),
            "ShadowScenePass.atlasPCF": lambda: (self.target.getDepthTexture(), self.pcfSampleState)
        }

