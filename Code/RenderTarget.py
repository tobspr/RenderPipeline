
from panda3d.core import GraphicsOutput, CardMaker, OmniBoundingVolume
from panda3d.core import AuxBitplaneAttrib, NodePath, OrthographicLens
from panda3d.core import Camera, Vec4, TransparencyAttrib, StencilAttrib
from panda3d.core import ColorWriteAttrib, DepthWriteAttrib, Texture  
from panda3d.core import WindowProperties, FrameBufferProperties, GraphicsPipe


from RenderTargetType import RenderTargetType
from MemoryMonitor import MemoryMonitor
from DebugObject import DebugObject
from Globals import Globals
from MemoryMonitor import MemoryMonitor
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

    numBuffersAllocated = 0

    def __init__(self, name="DefaultRT"):
        """ Creates a new RenderTarget with the given name. Use a
        descriptive name as it will show with this name in pstats """
        DebugObject.__init__(self, "RenderTarget")
        self._targets = {}
        self._bindMode = GraphicsOutput.RTMBindOrCopy
        self._depthBits = 8
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
        self._createOverlayQuad = True
        self._writeColor = True
        self._multisamples = 0
        self._engine = Globals.base.graphicsEngine
        self._active = False
        self._useTextureArrays = False
        self._haveColorAlpha = True
        self._internalBuffer = None
        self._rename(name)
        self.mute()

    def setCreateOverlayQuad(self, createQuad):
        """ When create quad is set to true, a fullscreen quad will be used to be
        able to directly apply a shader to it """
        self._createOverlayQuad = createQuad

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
        rendering to a texture array or 3D texture."""
        self._layers = layers
        if layers > 1:
            self._bindMode = GraphicsOutput.RTMBindLayered

    def setName(self, name):
        """ Sets the buffer name to identify it in pstats """
        self._name = name

    def setEnableTransparency(self, enabled=True):
        """ Sets wheter objects can be transparent in this buffer """
        self._enableTransparency = enabled

    def setSize(self, width, height=None):
        """ Sets the buffer size in pixels. -1 means as big as the current 
        window (default) """
        self._width = width

        if height is None:
            height = width

        self._height = height

    def setHalfResolution(self):
        """ Sets the buffer to render at half the size of the window """
        self._width = self._sourceWindow.getXSize() / 2
        self._height = self._sourceWindow.getYSize() / 2

    def setColorWrite(self, write):
        """ Sets wheter to write color """
        self._writeColor = write

    def setColorBits(self, colorBits):
        """ Sets the amount of color bits to request """
        self._colorBits = colorBits

    def setAuxBits(self, auxBits):
        """ Sets the amount  of auxiliary bits to request """
        self._auxBits = auxBits

    def setDepthBits(self, bits):
        """ Sets the amount of depth bits to request """
        self._depthBits = bits

    def setShaderInput(self, *args):
        """ This is a shortcut for setting shader inputs on the buffer """
        self.getQuad().setShaderInput(*args)

    def setShader(self, shader):
        """ This is a shortcut for setting shaders to the buffer """
        self.getQuad().setShader(shader)

    def getTarget(self, target):
        """ Returns the texture handle for the given target """
        return self._targets[target]

    def getColorTexture(self):
        """ Returns the handle to the color texture """
        return self.getTexture(RenderTargetType.Color)

    def getDepthTexture(self):
        """ Returns the handle to the depth texture """
        return self.getTexture(RenderTargetType.Depth)

    def getInternalBuffer(self):
        """ Returns the internal buffer object """
        return self._internalBuffer

    def getInternalRegion(self):
        """ Returns the internal display region, this can be used to set
        custom sort values."""
        return self._internalBuffer.getDisplayRegion(0)

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
        be set automatically (highly recommended) """
        self._sourceCam = sourceCam
        self._sourceWindow = sourceWin
        self._region = region

    def setBindModeLayered(self, layered=True):
        """ When rendering layered, you have to call this. This
        sets the internal bind mode for the RenderBuffer. When not using
        layered bind mode, the rendering might get very slow. """
        if layered:
            self._bindMode = GraphicsOutput.RTMBindLayered
        else:
            self._bindMode = GraphicsOutput.RTMBindOrCopy

    def addRenderTexture(self, targetType):
        """ Lower level function to add a new target. targetType should be
        a RenderTargetType """
        if targetType in self._targets:
            self.error("You cannot add another type of", targetType)
            return False

        self.debug("Adding render texture: ", targetType)
        self._targets[targetType] = Texture(self._name + "-Tex" + targetType)

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

    def addAuxTexture(self):
        """ Adds a single aux texture """
        self.addAuxTextures(1)

    def hasTarget(self, target):
        """ Check if a target is assigned to this target """
        return target in self._targets

    def hasAuxTextures(self):
        """ Returns wheter this target has at least 1 aux texture attached """
        return self.hasTarget(RenderTargetType.Aux0)

    def hasColorTexture(self):
        """ Returns wheter this target has a color texture attached """
        return self.hasTarget(RenderTargetType.Color)

    def hasDepthTexture(self):
        """ Returns wheter this target has a depth texture attached """
        return self.hasTarget(RenderTargetType.Depth)

    def _createBuffer(self):
        """ Internal method to create the buffer object """
        self._width = self._sourceWindow.getXSize(
        ) if self._width < 1 else self._width
        self._height = self._sourceWindow.getYSize(
        ) if self._height < 1 else self._height

        self.debug("Creating buffer")

        if not self._create():
            self.error("Failed to create buffer!")
            return False

        if self._region is None:
            self._region = self._internalBuffer.makeDisplayRegion()

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

        if self._createOverlayQuad:
            self._region.setCamera(bufferCamNode)
            self._region.setSort(5)

        # Set clears
        bufferRegion = self._internalBuffer.getDisplayRegion(0)
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

        bufferRegion = self._internalBuffer.getDisplayRegion(0)
        bufferRegion.setCamera(bufferCamNode)
        bufferRegion.setActive(1)
        self._setSizeShaderInput()

        self._active = True
        self._registerBuffer()

    def setActive(self, active):
        """ You can enable / disable the buffer with this. When disabled,
        shaders on this buffer aren't executed """
        if self._active is not active:
            self._internalBuffer.getDisplayRegion(
                0).setActive(active)
            # self._region.setActive(active)
            self._active = active

    def getQuad(self):
        """ Returns the quad-node path. You can use this to set attributes on it """
        return self._quad

    def getTexture(self, target):
        """ Returns the texture assigned to a target. The target should be a
        RenderTargetType """
        if target not in self._targets:
            self.error(
                "The target", target, "isn't bound to this RenderTarget!")
            return

        return self.getTarget(target)

    def _makeFullscreenQuad(self):
        """ Create a quad which fills the whole screen """
        cm = CardMaker("BufferQuad")
        cm.setFrameFullscreenQuad()
        quad = NodePath(cm.generate())
        quad.setDepthTest(0)
        quad.setDepthWrite(0)
        quad.setAttrib(TransparencyAttrib.make(TransparencyAttrib.MNone), 1000)
        quad.setColor(Vec4(1, 0.5, 0.5, 1))

        # Disable culling
        quad.node().setFinal(True)
        quad.node().setBounds(OmniBoundingVolume())
        quad.setBin("unsorted", 10)
        return quad

    def _makeFullscreenCam(self):
        """ Creates an orthographic camera for this buffer """
        bufferCam = Camera("BufferCamera")
        lens = OrthographicLens()
        lens.setFilmSize(2, 2)
        lens.setFilmOffset(0, 0)
        lens.setNearFar(-1000, 1000)
        bufferCam.setLens(lens)
        bufferCam.setCullBounds(OmniBoundingVolume())
        return bufferCam

    def _findRegionForCamera(self):
        """ Finds the assigned region of the supplied camera """
        for i in range(self._sourceWindow.getNumDisplayRegions()):
            dr = self._sourceWindow.getDisplayRegion(i)
            drcam = dr.getCamera()
            if (drcam == self._sourceCam):
                return dr
        return None

    def _correctClears(self):
        """ Setups the clear values correctly for the buffer region """
        region = self._internalBuffer.getDisplayRegion(0)

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
        self._internalBuffer.setClearDepthActive(clear)
        if clear:
            self._internalBuffer.setClearDepth(0.0)

    def setClearColor(self, clear=True, color=None):
        """ Adds a color clear """
        self.getInternalRegion().setClearColorActive(clear)
        self._internalBuffer.setClearColorActive(clear)

        if clear:
            if color is None:
                color = Vec4(0)
            self._internalBuffer.setClearColor(color)

    def removeQuad(self):
        """ Removes the fullscren quad after creation, this might be required
        when rendering to a scene which is not the main scene """
        self.getQuad().node().removeAllChildren()

    def _setSizeShaderInput(self):
        """ Makes the buffer size available as shader input in the shader """
        asInput = Vec4(1.0 / self._width, 1.0 / self._height, self._width, self._height)
        self.setShaderInput("bufferSize", asInput)

    def _registerBuffer(self):
        """ Internal method to register the buffer at the buffer viewer """
        BufferViewerGUI.registerBuffer(self._name, self)

    def isActive(self): 
        """ Returns wheter this buffer is currently active """
        return self._active

    def deleteBuffer(self):
        """ Deletes this buffer, restoring the previous state """
        self.warn("Todo:: Implement delete Buffer")
        MemoryMonitor.unregisterRenderTarget(self._name, self)
        self._engine.removeWindow(self._internalBuffer)
        self._active = False
        BufferViewerGUI.unregisterBuffer(self._name)

    def _create(self):
        """ Attempts to create this buffer """

        colorIsFloat = self._colorBits >= 16
        auxIsFloat = self._auxBits >= 16

        self.debug("Bitcount: color=" + str(self._colorBits) +
                   "; aux=" + str(self._auxBits) + "; depth=" + str(self._depthBits))

        # set wrap modes for color + auxtextures,
        # also set correct formats:
        # panda doesnt use sized formats automatically, this
        # gives problems when using imageLoad / imageStore
        prepare = [
            RenderTargetType.Color,
            RenderTargetType.Aux0,
            RenderTargetType.Aux1,
            RenderTargetType.Aux2,
            RenderTargetType.Aux3,
        ]

        for target in prepare:
            if not self.hasTarget(target):
                continue
            handle = self.getTarget(target)
            handle.setWrapU(Texture.WMClamp)
            handle.setWrapV(Texture.WMClamp)
            handle.setWrapW(Texture.WMClamp)
            handle.setMinfilter(Texture.FTLinear)
            handle.setMagfilter(Texture.FTLinear)
            handle.setAnisotropicDegree(0)

            handle.setXSize(self._width)
            handle.setYSize(self._height)

            if target == RenderTargetType.Color:
                if colorIsFloat:
                    handle.setComponentType(Texture.TFloat)

                if self._colorBits == 8:
                    if self._haveColorAlpha:
                        handle.setFormat(Texture.FRgba8)
                    else:
                        handle.setFormat(Texture.FRgb8)

                elif self._colorBits == 16:
                    if self._haveColorAlpha:
                        handle.setFormat(Texture.FRgba16)
                    else:
                        handle.setFormat(Texture.FRgb16)

                elif self._colorBits == 32:
                    if self._haveColorAlpha:
                        handle.setFormat(Texture.FRgba32)
                    else:
                        handle.setFormat(Texture.FRgb32)
            else:
                if auxIsFloat:
                    handle.setComponentType(Texture.TFloat)

                if self._auxBits == 8:
                    handle.setFormat(Texture.FRgba8)
                elif self._auxBits == 16:
                    handle.setFormat(Texture.FRgba16)
                elif self._auxBits == 32:
                    handle.setFormat(Texture.FRgba32)

            if self._layers > 1:
                if self._useTextureArrays:
                    handle.setup2dTextureArray(self._layers)
                else:
                    handle.setup3dTexture(self._layers)

        # set layers for depth texture
        if self._layers > 1 and self.hasTarget(RenderTargetType.Depth):
            if self._useTextureArrays:
                self.getTarget(RenderTargetType.Depth).setup2dTextureArray(
                    self._layers)
            else:
                self.getTarget(RenderTargetType.Depth).setup3dTexture(
                    self._layers)


        # Create buffer descriptors
        windowProps = WindowProperties.size(self._width, self._height)
        bufferProps = FrameBufferProperties()

        # Set color and alpha bits
        if self.hasTarget(RenderTargetType.Color):
            bufferProps.setRgbaBits(self._colorBits, self._colorBits, self._colorBits, self._colorBits if self._haveColorAlpha else 0)
            if colorIsFloat:
                bufferProps.setFloatColor(True)


        # Set aux bits
        if self.hasTarget(RenderTargetType.Aux0) and auxIsFloat:
            # FRAMEBUFFER INCOMPLETE when using this to render to a 3d texture
            # bufferProps.setAuxFloat(True)
            pass

        # Set depth bits and depth texture format
        if self.hasTarget(RenderTargetType.Depth):
            depthTarget = self.getTarget(RenderTargetType.Depth)

            bufferProps.setDepthBits(self._depthBits)
            bufferProps.setFloatDepth(True)


            if self._depthBits == 24:
                # depthTarget.setComponentType(Texture.TFloat)
                depthTarget.setFormat(Texture.FDepthComponent24)
            elif self._depthBits == 32:
                # depthTarget.setComponentType(Texture.TFloat)
                depthTarget.setFormat(Texture.FDepthComponent32)

            depthTarget.setXSize(self._width)
            depthTarget.setYSize(self._height)

        # We need no stencil (not supported yet)
        bufferProps.setStencilBits(0)

        numAuxtex = 0

        # Python really needs switch()
        # FIXME: Why is it 2 when only 1 AUX texture is attached?!
        if self.hasTarget(RenderTargetType.Aux3):
            numAuxtex = 3
        elif self.hasTarget(RenderTargetType.Aux2):
            numAuxtex = 3
        elif self.hasTarget(RenderTargetType.Aux1):
            numAuxtex = 2
        elif self.hasTarget(RenderTargetType.Aux0):
            numAuxtex = 1

        self.debug("Num Auxtex=", numAuxtex)

        # Add aux textures (either 8 or 16 bit)
        if auxIsFloat:
            bufferProps.setAuxHrgba(numAuxtex)
        else:
            bufferProps.setAuxRgba(numAuxtex)

        bufferProps.setMultisamples(self._multisamples)

        # Register the target for the memory monitoring
        MemoryMonitor.addRenderTarget(self._name, self)

        # Create internal graphics output
        self._internalBuffer = self._engine.makeOutput(
            self._sourceWindow.getPipe(), self._name, 1,
            bufferProps, windowProps,
            GraphicsPipe.BFRefuseWindow | GraphicsPipe.BFResizeable,
            self._sourceWindow.getGsg(), self._sourceWindow)

        if self._internalBuffer is None:
            self.error("Failed to create buffer :(")
            return False

        # Add render targets
        if self.hasTarget(RenderTargetType.Depth):
            self._internalBuffer.addRenderTexture(
                self.getTarget(RenderTargetType.Depth), self._bindMode,
                GraphicsOutput.RTPDepth)

        if self.hasTarget(RenderTargetType.Color):
            self._internalBuffer.addRenderTexture(
                self.getTarget(RenderTargetType.Color), self._bindMode,
                GraphicsOutput.RTPColor)

        modes = [
            (RenderTargetType.Aux0, GraphicsOutput.RTPAuxHrgba0,
             GraphicsOutput.RTPAuxRgba0),
            (RenderTargetType.Aux1, GraphicsOutput.RTPAuxHrgba1,
             GraphicsOutput.RTPAuxRgba1),
            (RenderTargetType.Aux2, GraphicsOutput.RTPAuxHrgba2,
             GraphicsOutput.RTPAuxRgba2),
            (RenderTargetType.Aux3, GraphicsOutput.RTPAuxHrgba3,
             GraphicsOutput.RTPAuxRgba3),
        ]


        for target, floatMode, normalMode in modes:
            if self.hasTarget(target):
                self._internalBuffer.addRenderTexture(
                    self.getTarget(target), self._bindMode,
                    floatMode if auxIsFloat else normalMode)

        # Increment global sort counter
        RenderTarget.numBuffersAllocated += 1
        self._sort = -300 + RenderTarget.numBuffersAllocated * 10

        self.debug("our sort value is", self._sort)
        self._internalBuffer.setSort(self._sort)
        self._internalBuffer.disableClears()
        self._internalBuffer.getDisplayRegion(0).disableClears()

        for i in xrange(16):
            self._internalBuffer.setClearActive(i, False)
            self._internalBuffer.getDisplayRegion(0).setClearActive(i, False)

        self._internalBuffer.setClearStencilActive(False)

        if self.hasTarget(RenderTargetType.Depth):
            depthTarget = self.getTarget(RenderTargetType.Depth)

            if self._depthBits == 24:
                # depthTarget.setComponentType(Texture.TFloat)
                depthTarget.setFormat(Texture.FDepthComponent24)
            elif self._depthBits == 32:
                # depthTarget.setComponentType(Texture.TFloat)
                depthTarget.setFormat(Texture.FDepthComponent32)

        return True


    def __repr__(self):
        """ Returns a representative string of this instance """
        return "RenderTarget('" + self._name + "')"

