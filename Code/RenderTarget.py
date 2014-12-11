
from panda3d.core import GraphicsOutput, CardMaker, OmniBoundingVolume
from panda3d.core import AuxBitplaneAttrib, NodePath, OrthographicLens
from panda3d.core import Camera, Vec4, TransparencyAttrib, StencilAttrib
from panda3d.core import ColorWriteAttrib, DepthWriteAttrib
from RenderBuffer import RenderBuffer
from RenderTargetType import RenderTargetType
from DebugObject import DebugObject
from Globals import Globals
from GUI.BufferViewerGUI import BufferViewerGUI


class RenderTarget(DebugObject):

    """ This is a high level interface for creating buffers
    and render-to-textures. It internally wraps arround RenderBuffer
    but also takes care of sorting and clearing, and especially
    setting up the scene rendering when using render-to-texture.

    After creating a RenderTarget, you have to add targets with
    addRenderTexture, with target beeing RenderTargetType.XXX. There
    are shortcuts for this like addColorTexture and addDepthTexture.

    When not setting a size, the size will be the size of the specified
    window (set with setSource, default is base.win). Using setSize(-1, -1)
    has the same effect.

    Then you can either call prepareSceneRender(), which will render
    the scene of the sourceCam (set with setSource, default is base.cam)
    to the buffer, or call prepareOffscreenBuffer(), which will just
    create an offscreen buffer.

    A sample setup might look like this:

        target = RenderTarget("My Fancy Target")

        # This adds RenderTargetType.Color and RenderTargetType.Depth
        target.addColorAndDepth()

        # This adds RenderTargetType.Aux0 and RenderTargetType.Aux1
        target.addAuxTextures(2)
        target.setAuxBits(16)
        target.setColorBits(16)
        target.setDepthBits(32)
        target.setSize(-1, -1) # can be omitted
        target.prepareSceneRender()

    """

    def __init__(self, name="DefaultRT"):
        """ Creates a new RenderTarget with the given name. Use a
        descriptive name as it will show with this name in pstats """
        DebugObject.__init__(self, "RenderTarget")
        self._targetFlags = {}
        self._bindMode = GraphicsOutput.RTMBindOrCopy
        self._depthbits = 8
        self._buffer = None
        self._quad = None
        self._sourceCam = Globals.base.cam
        self._sourceWindow = Globals.base.win
        self._width = -1
        self._height = -1
        self._name = name
        self._colorBits = 8
        self._auxBits = 8
        self._region = self._findRegionForCamera()
        self._enableTransparency = False
        self._layers = 0
        self._writeColor = True
        self._multisamples = 0
        self._engine = Globals.base.graphicsEngine
        self._active = False
        self._useTextureArrays = False
        self._haveColorAlpha = True
        self._rename(name)

        self.mute()

    def setHaveColorAlpha(self, color_alpha):
        """ Sets wheter the color buffer has an alpha channel or not """
        self._haveColorAlpha = color_alpha

    def setUseTextureArrays(self, state=True):
        """ Makes the render buffer use a 2D texture array when rendering 
        layers. Otherwise a 3D Texture is choosen """
        self._useTextureArrays = state

    def setMultisamples(self, samples):
        """ Sets the amount of multisamples to use """
        self._multisamples = samples

    def setEngine(self, engine):
        """ Sets the graphic engine to use """
        self._engine = engine

    def setLayers(self, layers):
        """ Sets the number of layers. When greater than 1, this enables
        rendering to a texture array """
        self._layers = layers
        if layers > 1:
            self._bindMode = GraphicsOutput.RTMBindLayered

    def setName(self, name):
        """ Sets the buffer name to identify in pstats """
        self._name = name

    def setEnableTransparency(self, enabled=True):
        """ Sets wheter objects can be transparent in this buffer """
        self._enableTransparency = enabled

    def setSize(self, width, height=None):
        """ Sets the buffer size in pixels. -1 means as big
        as the current window """
        self._width = width

        if height is None:
            height = width

        self._height = height

    def setColorWrite(self, write):
        """ Sets wheter to write color """
        self._writeColor = write

    def setColorBits(self, colorBits):
        """ Sets the required color bits """
        self._colorBits = colorBits

    def setAuxBits(self, auxBits):

        self._auxBits = auxBits

    def setDepthBits(self, bits):
        """ Sets the required depth bits """
        self._depthbits = bits

    def setShaderInput(self, name, val):
        """ This is a shortcut for setting shader inputs of the buffer """
        self.getQuad().setShaderInput(name, val, 200)

    def setShader(self, shader):
        """ This is a shortcut for setting shaders to the buffer """
        self.getQuad().setShader(shader)

    def getColorTexture(self):
        """ Returns the handle to the color texture """
        return self.getTexture(RenderTargetType.Color)

    def getDepthTexture(self):
        """ Returns the handle to the depth texture """
        return self.getTexture(RenderTargetType.Depth)

    def getInternalBuffer(self):
        """ Returns the internal buffer object """
        return self._buffer.getInternalBuffer()

    def getInternalRegion(self):
        """ Returns the internal display region, e.g. if you need to set
        custom sort values """
        return self.getInternalBuffer().getDisplayRegion(0)

    def getAuxTexture(self, index=0):
        """ Returns the n-th aux texture, starting at 0 """
        assert(index < 4)
        auxTextures = [
            RenderTargetType.Aux0,
            RenderTargetType.Aux1,
            RenderTargetType.Aux2,
            RenderTargetType.Aux3
        ]
        return self.getTexture(auxTextures[index])

    def setSource(self, sourceCam, sourceWin, region=None):
        """ Sets source window and camera. When region is None, it will
        be set automatically (highly recommended!!) """
        self._sourceCam = sourceCam
        self._sourceWindow = sourceWin
        self._region = region

    def setBindModeLayered(self, layered=True):
        """ When rendering layered, you have to call this. This
        sets the internal bind mode for the RenderBuffer """
        if layered:
            self._bindMode = GraphicsOutput.RTMBindLayered
        else:
            self._bindMode = GraphicsOutput.RTMBindOrCopy

    def addRenderTexture(self, ttype):
        """ Lower level function to add a new target. ttype should be
        a RenderTargetType """
        if ttype in self._targetFlags:
            self.error("You cannot add another type of", ttype)
            return False

        self.debug("Adding render texture: ", ttype)
        self._targetFlags[ttype] = None

    def addColorTexture(self):
        """ Adds a color target """
        return self.addRenderTexture(RenderTargetType.Color)

    def addDepthTexture(self):
        """ Adds a depth target """
        return self.addRenderTexture(RenderTargetType.Depth)

    def addColorAndDepth(self):
        """ Adds a color and depth target """
        self.addColorTexture()
        self.addDepthTexture()

    def addAuxTextures(self, num):
        """ Adds n aux textures. num should be between 1 and 4 """
        assert(num > 0 and num <= 4)
        targets = [
            RenderTargetType.Aux0,
            RenderTargetType.Aux1,
            RenderTargetType.Aux2,
            RenderTargetType.Aux3,
        ]

        for i in range(num):
            self.addRenderTexture(targets[i])

    def hasTarget(self, target):
        """ Check if a target is assigned to this target """
        return target in self._targetFlags

    def hasAuxTextures(self):
        """ Wheter this target has at least 1 aux texture attached """
        return self.hasTarget(RenderTargetType.Aux0)

    def hasColorTexture(self):
        """ Wheter this target has a color texture attached """
        return self.hasTarget(RenderTargetType.Color)

    def hasDepthTexture(self):
        """ Wheter this target has a depth texture attached """
        return self.hasTarget(RenderTargetType.Depth)

    def _createBuffer(self):
        """ Internal method to create the buffer object """
        wantedX = self._sourceWindow.getXSize(
        ) if self._width < 1 else self._width
        wantedY = self._sourceWindow.getYSize(
        ) if self._height < 1 else self._height

        self.debug("Creating buffer of size", wantedX, "x", wantedY)

        self._buffer = RenderBuffer()
        self._buffer.setName("[FBO] " + self._name)
        self._buffer.setSize(wantedX, wantedY)
        self._buffer.setWindow(self._sourceWindow)
        self._buffer.setColorBits(self._colorBits)
        self._buffer.setAuxBits(self._auxBits)
        self._buffer.setDepthBits(self._depthbits)
        self._buffer.setBindMode(self._bindMode)
        self._buffer.setLayers(self._layers)
        self._buffer.setMultisamples(self._multisamples)
        self._buffer.setEngine(self._engine)
        self._buffer.setHaveColorAlpha(self._haveColorAlpha)

        for flag in self._targetFlags.keys():
            self._buffer.addTarget(flag)

        if not self._buffer.create():
            self.error("Failed to create buffer. Damned.")
            return False

        if self._region is None:
            self._region = self._buffer.getInternalBuffer().makeDisplayRegion()

    def getRegion(self):
        """ Returns the display region of this target. You can use
        this to set custom clears """
        return self._region

    def prepareSceneRender(self):
        """ Renders the scene of the source camera to the buffer. See the
        documentation of this class for further information """

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
            cs.setAttrib(
                TransparencyAttrib.make(TransparencyAttrib.MNone), 100)

        if not self._writeColor:
            cs.setAttrib(ColorWriteAttrib.make(ColorWriteAttrib.COff), 100)

        self._sourceCam.node().setInitialState(cs.getState())

        # Set new camera
        bufferCam = self._makeFullscreenCam()
        bufferCamNode = self._quad.attachNewNode(bufferCam)
        self._region.setCamera(bufferCamNode)
        self._region.setSort(5)

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
                bufferRegion.setClearValue(
                    targetBindPos, Vec4(0.5, 0.5, 1.0, 0.0))

        self._region.disableClears()

        bufferRegion.setCamera(self._sourceCam)
        bufferRegion.setActive(1)
        # bufferRegion.setClearDepthActive(False)
        bufferRegion.setSort(20)

        self._setSizeShaderInput()

        self._active = True
        self._registerBuffer()

    def prepareOffscreenBuffer(self):
        """ Creates an offscreen buffer for this target """

        self.debug("Preparing offscreen buffer")

        # Init buffer object
        self._createBuffer()

        # Prepare fullscreen quad
        self._quad = self._makeFullscreenQuad()

        # Prepare fullscreen camera
        bufferCam = self._makeFullscreenCam()
        initialState = NodePath("is")

        if not self._writeColor:
            initialState.setAttrib(
                ColorWriteAttrib.make(ColorWriteAttrib.COff), 1000)

        initialState.setAttrib(
            DepthWriteAttrib.make(DepthWriteAttrib.MNone), 1000)

        bufferCam.setInitialState(initialState.getState())

        bufferCamNode = self._quad.attachNewNode(bufferCam)

        bufferRegion = self._buffer.getInternalBuffer().getDisplayRegion(0)
        bufferRegion.setCamera(bufferCamNode)
        bufferRegion.setActive(1)

        self._setSizeShaderInput()

        self._active = True
        self._registerBuffer()

    def setActive(self, active):
        """ You can enable / disable the buffer with this. When disabled,
        shaders on this buffer aren't executed """
        if self._active is not active:
            self._buffer.getInternalBuffer().getDisplayRegion(
                0).setActive(active)
            self._region.setActive(active)
            self._active = active

    def getQuad(self):
        """ Returns the quad-node path. You can use this to set shader inputs
        and so on, although you should use setShaderInput for that """
        return self._quad

    def getTexture(self, target):
        """ Returns the texture assigned to a target. target should be a
        RenderTargetType """
        if target not in self._targetFlags:
            self.error(
                "The target", target, "isn't bound to this RenderTarget!")
            return

        return self._buffer.getTarget(target)

    def _makeFullscreenQuad(self):
        """ Create a quad which fills the full screen """
        cm = CardMaker("BufferQuad")
        cm.setFrameFullscreenQuad()
        quad = NodePath(cm.generate())
        quad.setDepthTest(0)
        quad.setDepthWrite(0)
        quad.setAttrib(TransparencyAttrib.make(TransparencyAttrib.MNone), 1000)
        quad.setColor(Vec4(1, 0.5, 0.5, 1))

        # No culling check
        quad.node().setFinal(True)
        quad.node().setBounds(OmniBoundingVolume())
        quad.setBin("unsorted", 10)
        return quad

    def _makeFullscreenCam(self):
        """ Create a orthographic camera for this buffer """
        bufferCam = Camera("BufferCamera")
        lens = OrthographicLens()
        lens.setFilmSize(2, 2)
        lens.setFilmOffset(0, 0)
        lens.setNearFar(-1000, 1000)
        bufferCam.setLens(lens)
        bufferCam.setCullBounds(OmniBoundingVolume())
        return bufferCam

    def _findRegionForCamera(self):
        """ Finds the region of the supplied camera """
        for i in range(self._sourceWindow.getNumDisplayRegions()):
            dr = self._sourceWindow.getDisplayRegion(i)
            drcam = dr.getCamera()
            if (drcam == self._sourceCam):
                return dr
        return None

    def _correctClears(self):
        """ Setups the clear values correctly """
        region = self._buffer.getInternalBuffer().getDisplayRegion(0)

        clears = []

        for i in range(GraphicsOutput.RTPCOUNT):
            active, value = self._sourceWindow.getClearActive(
                i), self._sourceWindow.getClearValue(i)

            if not active:
                active, value = self._region.getClearActive(
                    i), self._region.getClearValue(i)

            region.setClearActive(i, active)
            region.setClearValue(i, value)

        return clears

    def setClearDepth(self, clear=True):
        """ Adds a depth clear """
        self.getInternalRegion().setClearDepthActive(clear)
        if clear:
            self.getInternalBuffer().setClearDepth(0.0)

    def setClearColor(self, clear=True, color=None):
        """ Adds a color clear """
        self.getInternalRegion().setClearColorActive(clear)
        if clear:
            if color is None:
                color = Vec4(0)
            self.getInternalBuffer().setClearColor(color)

    def setClearAux(self, auxNumber, clear=True):
        """ Adds a color clear """
        self.getInternalRegion().setClearActive(auxNumber, clear)

    def removeQuad(self):
        """ Removes the fullscren quad after creation, this might be required
        when rendering to a scene which is not the main scene """
        self.getQuad().node().removeAllChildren()

    def _setSizeShaderInput(self):
        """ Makes the buffer size available as shader input in the shader """
        bufferSize = self._buffer.getSize()
        asInput = Vec4(
            1.0 / bufferSize.x, 1.0 / bufferSize.y, bufferSize.x, bufferSize.y)
        self.setShaderInput("bufferSize", asInput)

    def _registerBuffer(self):
        """ Internal method to register the buffer at the buffer viewer """
        BufferViewerGUI.registerBuffer(self._name, self)

    def _unregisterBuffer(self):
        """ Internal method to unregister the buffer from the buffer viewer """
        BufferViewerGUI.unregisterBuffer(self._name)

    def isActive(self):
        """ Returns wheter this buffer is currently active """
        return self._active

    def updateSize(self):
        """ Updates the size of this render target. TODO """
        raise NotImplementedError("Not working yet")

        """
        wantedX = self._sourceWindow.getXSize(
        ) if self._width < 1 else self._width
        wantedY = self._sourceWindow.getYSize(
        ) if self._height < 1 else self._height
        self._buffer.setSize(wantedX, wantedY)
        self._setSizeShaderInput()
        """

    def deleteBuffer(self):
        """ Deletes this buffer, restoring the previous state """
        self.warn("Todo:: Implement delete Buffer")

        self._engine.removeWindow(self._buffer.getInternalBuffer())
        del self._buffer

        self._active = False
        self._unregisterBuffer()

    def __repr__(self):
        """ Returns a representative string of this instance """
        return "RenderTarget('" + self._name + "')"
