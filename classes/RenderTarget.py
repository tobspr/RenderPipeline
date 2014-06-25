
from panda3d.core import GraphicsOutput, CardMaker, OmniBoundingVolume
from panda3d.core import AuxBitplaneAttrib, NodePath, OrthographicLens
from panda3d.core import Camera, Vec4, TransparencyAttrib, StencilAttrib
from RenderBuffer import RenderBuffer
from RenderTargetType import RenderTargetType
from DebugObject import DebugObject

class RenderTarget(DebugObject):

    def __init__(self, name="DefaultRT"):
        DebugObject.__init__(self, "RenderTarget")
        self._targetFlags = {}
        self._bindMode = GraphicsOutput.RTMBindOrCopy
        self._depthbits = 24
        self._buffer = None
        self._quad = None
        self._sourceCam = base.cam
        self._sourceWindow = base.win
        self._width = -1
        self._height = -1
        self._name = name
        self._colorBits = 8
        self._auxBits = 8
        self._region = self._findRegionForCamera()
        self._enableTransparency = False


    # Sets the buffer name to identify in pstats
    def setName(self, name):
        self._name = name


    # Sets wheter objects can be transparent
    def setEnableTransparency(self, enabled=True):
        self._enableTransparency = enabled

    # Sets the buffer size
    # -1 means as big as the current window
    def setSize(self, width, height):
        self._width = width
        self._height = height

    # Sets the required color bits
    def setColorBits(self, colorBits):
        self._colorBits = colorBits

    # Sets the required aux bits
    def setAuxBits(self, auxBits):
        self._auxBits = auxBits

    # Sets source window and camera
    def setSource(self, sourceCam, sourceWin, region=None):
        self._sourceCam = sourceCam
        self._sourceWindow = sourceWin
        
        if region is not None:
            self._region = region
        else:
            self._region = self._findRegionForCamera()

    # Wheter to render layered
    def setBindModeLayered(self, layered=True):
        self._bindMode = GraphicsOutput.RTMBindLayered if layered else GraphicsOutput.RTMBindOrCopy

    # How many depth bits to use
    def setDepthBits(self, bits):
        self._depthbits = bits

    # Adds a new target to render to
    def addRenderTexture(self, ttype):
        if ttype in self._targetFlags:
            self.error("You cannot add another type of",ttype)
            return False

        self.debug("Adding render texture: ", ttype)
        self._targetFlags[ttype] = None # initialize empty

    # Check if the target is assigned
    def hasTarget(self, target):
        return target in self._targetFlags

    # Internal method to create the buffer object
    def _createBuffer(self):
        wantedX = self._sourceWindow.getXSize() if self._width < 1 else self._width
        wantedY = self._sourceWindow.getYSize() if self._height < 1 else self._height

        self.debug("Creating buffer of size", wantedX, "x",wantedY)

        self._buffer = RenderBuffer()
        self._buffer.setName("RTarget-" + self._name)
        self._buffer.setSize(wantedX, wantedY)
        self._buffer.setWindow(self._sourceWindow)
        self._buffer.setColorBits(self._colorBits)
        self._buffer.setAuxBits(self._auxBits)
        self._buffer.setDepthBits(self._depthbits)
        self._buffer.setBindMode(self._bindMode)

        for flag in self._targetFlags.keys():
            self._buffer.addTarget(flag)

        if not self._buffer.create():
            print "Failed to create buffer. Damned."
            return False

    # Renders the scene into the aquired buffers
    def prepareSceneRender(self):

        self.debug("Preparing scene render")

        # Init buffer object
        self._createBuffer()

        # Prepare fullscreen quad
        self._quad = self._makeFullscreenQuad()

        # Prepare initial state
        cs = NodePath("InitialStateDummy")
        cs.setState(self._sourceCam.node().getInitialState())
        if self.hasTarget(RenderTargetType.Aux0):
            cs.setAttrib(AuxBitplaneAttrib.make(self._auxBits), 20)

        cs.setAttrib(StencilAttrib.makeOff(), 20)

        if not self._enableTransparency:
            cs.setAttrib(TransparencyAttrib.make(TransparencyAttrib.MNone), 20)
        self._sourceCam.node().setInitialState(cs.getState())

        # Set new camera
        bufferCam = self._makeFullscreenCam()
        bufferCamNode = self._quad.attachNewNode(bufferCam)
        self._region.setCamera(bufferCamNode)

        # Set clears
        bufferRegion = self._buffer.getInternalBuffer().getDisplayRegion(0)


        self._correctClears()

        bufferRegion.setClearStencilActive(False)
        # self._sourceWindow.setClearStencilActive(False)

        # Set aux clears
        targetCheck = [
            (RenderTargetType.Aux0, GraphicsOutput.RTPAuxRgba0),
            (RenderTargetType.Aux1, GraphicsOutput.RTPAuxRgba1),
            (RenderTargetType.Aux2, GraphicsOutput.RTPAuxRgba2),
            (RenderTargetType.Aux3, GraphicsOutput.RTPAuxRgba3),
        ]
        for target, targetBindPos in targetCheck:
            if self.hasTarget(target):
                bufferRegion.setClearActive(targetBindPos, 1)
                bufferRegion.setClearValue(targetBindPos, Vec4(0.5, 0.5, 1.0, 0.0))

        self._region.disableClears()

        bufferRegion.setCamera(self._sourceCam)
        bufferRegion.setActive(1)
        # bufferRegion.setClearDepthActive(False)
        bufferRegion.setSort(20)        

        self._setSizeShaderInput()


    # Creates the buffer in an offscreen window
    def prepareOffscreenBuffer(self):

        self.debug("Preparing offscreen buffer")

        # Init buffer object
        self._createBuffer()

        # Prepare fullscreen quad
        self._quad = self._makeFullscreenQuad()

        # Prepare fullscreen camera
        bufferCam = self._makeFullscreenCam()
        bufferCamNode = self._quad.attachNewNode(bufferCam)

        bufferRegion = self._buffer.getInternalBuffer().getDisplayRegion(0)
        bufferRegion.setCamera(bufferCamNode)
        bufferRegion.setActive(1)


    # Wheter this buffer should be rendered or not
    def setActive(self, active):
        self._buffer.getInternalBuffer().getDisplayRegion(0).setActive(active)

    # Returns the quad to apply a shader to
    def getQuad(self):
        return self._quad

    # Returns the texture assigned to a target
    def getTexture(self, target):
        if target not in self._targetFlags:
            self.error("The target",target,"isn't bound to this RenderTarget!")
            return

        return self._buffer.getTarget(target)


    # Quad which fills the whole screen
    def _makeFullscreenQuad(self):
        cm = CardMaker("BufferQuad")
        cm.setFrameFullscreenQuad()
        quad = NodePath(cm.generate())
        quad.setDepthTest(0)
        quad.setDepthWrite(0)
        quad.setAttrib(TransparencyAttrib.make(TransparencyAttrib.MNone))
        quad.setColor(Vec4(1, 0.5, 0.5, 1))

        # No culling check
        quad.node().setFinal(True)
        quad.node().setBounds(OmniBoundingVolume())
        quad.setBin("unsorted", 10)
        return quad

    # Buffer camera
    def _makeFullscreenCam(self):
        bufferCam = Camera("BufferCamera")
        lens = OrthographicLens()
        lens.setFilmSize(2, 2)
        lens.setFilmOffset(0, 0)
        lens.setNearFar(-1000, 1000)
        bufferCam.setLens(lens)
        bufferCam.setCullBounds(OmniBoundingVolume())
        return bufferCam

    # Finds the region for the supplied camera
    def _findRegionForCamera(self):
        for i in range(self._sourceWindow.getNumDisplayRegions()):
            dr = self._sourceWindow.getDisplayRegion(i)
            drcam = dr.getCamera()
            if (drcam == self._sourceCam): return dr

        return None


    # Setups the clear values correctly
    def _correctClears(self):
        region = self._buffer.getInternalBuffer().getDisplayRegion(0)

        clears = []
        for i in range(GraphicsOutput.RTPCOUNT):
            active, value = self._sourceWindow.getClearActive(i), self._sourceWindow.getClearValue(i)
            if not active:
                active, value = self._region.getClearActive(i), self._region.getClearValue(i)
            region.setClearActive(i, active)
            region.setClearValue(i, value)


        return clears

    # Makes the buffer size available in the shader
    def _setSizeShaderInput(self):
        bufferSize = self._buffer.getSize()
        asInput = Vec4(1.0 / bufferSize.x, 1.0 / bufferSize.y, bufferSize.x, bufferSize.y)
        # self.debug("Setting shader input 'bufferSize' as",asInput)
        self._quad.setShaderInput("bufferSize", asInput)

    # Updates the size
    def updateSize(self):
        wantedX = self._sourceWindow.getXSize() if self._width < 1 else self._width
        wantedY = self._sourceWindow.getYSize() if self._height < 1 else self._height
        self._buffer.setSize(wantedX, wantedY)
        self._setSizeShaderInput()