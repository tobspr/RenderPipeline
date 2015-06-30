
from panda3d.core import NodePath, Camera, SamplerState, Shader
from panda3d.core import ColorWriteAttrib, Vec4, BitMask32

from ..Globals import Globals
from ..RenderPass import RenderPass
from ..RenderTarget import RenderTarget

class ShadowScenePass(RenderPass):

    """ This pass manages rendering the scene from the perspective of the shadow
    sources to generate the shadow maps. It also handles creating and managing
    the different regions of the shadow atlas, aswell as the initial state of
    all cameras assigned to the regions """

    def __init__(self):
        RenderPass.__init__(self)

        self.maxRegions = 8
        self.shadowScene = Globals.base.render

    def setMaxRegions(self, maxRegions):
        """ Sets the maximum amount of regions the atlas has. This is usually
        equal to the maximum number of shadow updates per frame """
        self.maxRegions = maxRegions

    def getID(self):
        return "ShadowScenePass"

    def getRequiredInputs(self):
        return {
            "numUpdates": "Variables.numShadowUpdates",
            "updateSources": "Variables.shadowUpdateSources" 
        }

    def setShaders(self):
        casterShader = Shader.load(Shader.SLGLSL,
            "Shader/DefaultShaders/ShadowCasting/vertex.glsl",
            "Shader/DefaultShaders/ShadowCasting/fragment.glsl")
        initialState = NodePath("ShadowCasterState")
        initialState.setShader(casterShader, 100)
        initialState.setAttrib(ColorWriteAttrib.make(ColorWriteAttrib.COff))
        for camera in self.shadowCameras:
            camera.node().setTagState("Default", initialState.getState())

        casterShaderTransparent = Shader.load(Shader.SLGLSL,
            "Shader/DefaultShaders/TransparentShadowCasting/vertex.glsl",
            "Shader/DefaultShaders/TransparentShadowCasting/fragment.glsl")
        initialState = NodePath("ShadowCasterStateTransparent")
        initialState.setShader(casterShaderTransparent, 100)
        initialState.setAttrib(ColorWriteAttrib.make(ColorWriteAttrib.COff))
        for camera in self.shadowCameras:
            camera.node().setTagState("Transparent", initialState.getState()) 

        return [casterShader, casterShaderTransparent]

    def setSize(self, size):
        """ Sets the shadow atlas size """
        self.size = size

    def setActiveRegionCount(self, activeCount):
        """ Sets the number of active regions, disabling all other regions. If the
        count is less than 1, completely disables the pass """


        if activeCount < 1:
            self.target.setActive(False)
            for region in self.renderRegions:
                region.setActive(False)

        else:
            self.target.setActive(True)
            for index, region in enumerate(self.renderRegions):
                if index < activeCount:
                    region.setActive(True)
                    pass
                else:
                    region.setActive(False)

    def setRegionDimensions(self, index, l, r, b, t):
        """ Sets the dimensions of the n-th region to the given dimensions """
        self.renderRegions[index].setDimensions(l, r, b, t)

    def getRegionCamera(self, index):
        """ Returns the camera of the n-th region """
        return self.shadowCameras[index]

    def create(self):
        # Create the atlas target
        self.target = RenderTarget("ShadowAtlas")
        self.target.setSize(self.size)
        self.target.addDepthTexture()
        self.target.setDepthBits(32)
        self.target.setColorWrite(False)
        self.target.setCreateOverlayQuad(False)
        # self.target.setActive(False)
        self.target.setSource(
            NodePath(Camera("tmp")), Globals.base.win)

        self.target.prepareSceneRender()
        self.target.setClearDepth(False)


        # Set the appropriate filter modes
        dTex = self.target.getDepthTexture()
        dTex.setWrapU(SamplerState.WMClamp)
        dTex.setWrapV(SamplerState.WMClamp)

        # Remove the default postprocess quad
        # self.target.getQuad().node().removeAllChildren()
        # self.target.getInternalRegion().setSort(-200)
        self.target.getInternalRegion().disableClears()
        self.target.getInternalBuffer().disableClears()
        # self.target.getInternalBuffer().setSort(-300)


        # Create default initial state
        initialState = NodePath("InitialState")
        initialState.setAttrib(ColorWriteAttrib.make(ColorWriteAttrib.COff))

        # Create a camera for each update
        self.shadowCameras = []
        for i in xrange(self.maxRegions):
            shadowCam = Camera("ShadowComputeCamera")
            shadowCam.setTagStateKey("ShadowPassShader")
            shadowCam.setInitialState(initialState.getState())
            shadowCam.setCameraMask(BitMask32.bit(3))
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
            # dr.setClearColorActive(False)
            # dr.setClearColor(Vec4(1,1,1,1))
            dr.setCamera(self.shadowCameras[i])
            dr.setActive(False)
            self.renderRegions.append(dr)

        self.pcfSampleState = SamplerState()
        self.pcfSampleState.setMinfilter(SamplerState.FTShadow)
        self.pcfSampleState.setMagfilter(SamplerState.FTShadow)
        self.pcfSampleState.setWrapU(SamplerState.WMClamp)
        self.pcfSampleState.setWrapV(SamplerState.WMClamp)

        # Globals.render.setTag("ShadowPassShader", "Default")

    def setShaderInput(self, name, val, *args):
        self.shadowScene.setShaderInput(name, val, *args)

    def getOutputs(self):
        return {
            "ShadowScenePass.atlas": lambda: self.target.getDepthTexture(),
            "ShadowScenePass.atlasPCF": lambda: (self.target.getDepthTexture(), self.pcfSampleState),
        }

