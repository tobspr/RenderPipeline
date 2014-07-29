
from panda3d.core import GraphicsOutput, Texture, WindowProperties
from panda3d.core import FrameBufferProperties, GraphicsPipe, Vec2
from RenderTargetType import RenderTargetType
from DebugObject import DebugObject
from Globals import Globals

# Wrapper arround GraphicsBuffer


class RenderBuffer(DebugObject):

    """ Low level buffer wrapper to create buffers and render-to-texture.
    This class is wrapped by RenderTarget, and not indented for public use. """

    # Store the number of buffers already allocated, to assign
    # correct sort values
    numBuffersAllocated = 0

    def __init__(self, name="RB"):
        """ Creates a new render buffer with the given name. The name should
        be descriptive as it will shown in pstats. """
        DebugObject.__init__(self, "RenderBuffer")
        self._name = name
        self._width = 0
        self._height = 0
        self._colorBits = 8
        self._auxBits = 8
        self._bindMode = GraphicsOutput.RTMBindOrCopy
        self._depthBits = 0
        self._internalBuffer = None
        self._targets = {}
        self._win = None
        self._layers = 0
        self._sort = 0
        self._multisamples = 0

        self.mute()

    def setLayers(self, layers):
        """ Set the number of layers to render, or 1 to not use layered 
        rendering. """
        self._layers = layers

    def setMultisamples(self, samples):
        """ Sets the amount of multisamples to use """
        self._multisamples = samples

    def setName(self, name):
        """ Sets the name of the buffer """
        self._name = name
        self._rename(name)

    def setWindow(self, window):
        """ Sets the target window of the buffer """
        self._win = window

    def setSize(self, width, height):
        """ Sets the size of the buffer in pixels """
        self._width = width
        self._height = height

        if self._internalBuffer is not None:
            self._internalBuffer.setSize(width, height)

    def getSize(self):
        """ Returns the size of the buffer in pixels """
        return Vec2(self._width, self._height)

    def setColorBits(self, colorBits):
        """ Set the minimum required color bits """
        self._colorBits = colorBits

    def setAuxBits(self, auxBits):
        """ Set the minimum required aux bits """
        self._auxBits = auxBits

    def addTarget(self, target):
        """ Adds a new target to render to. Target should be a RenderTargetType
        like RenderTargetType.Color """
        if target in self._targets:
            self.error("You cannot add another target of type", target)
            return

        self._targets[target] = Texture(self._name + "-Tex" + target)

    def setBindMode(self, bindMode):
        """ Sets the bind mode. When rendering layered, you have to set
        the bind mode to GraphicsOutput.RTMBindLayered, otherwise you can
        leave it default (GraphicsOutput.RTMBindOrCopy). In some special
        case you may force copying the buffers back to the ram with
        GraphicsOutput.RTMCopyTexture or RTMCopyRam """
        self._bindMode = bindMode

    def setDepthBits(self, depthBits):
        """ Sets the minimum required depth bits """
        self._depthBits = depthBits

    def getInternalBuffer(self):
        """ Returns a handle to the internal buffer object """
        return self._internalBuffer

    def hasTarget(self, target):
        """ Returns if this buffer already has a target of the given type """
        return target in self._targets

    def getTarget(self, target):
        """ Returns the texture object for the given target """
        return self._targets[target]

    def getSort(self):
        """ Returns the assigned sort value for this buffer. Only call
        this *after* the create() call, otherwise it will return 0. """
        return self._sort

    def create(self):
        """ Attempts to create this buffer """

        colorIsFloat = self._colorBits >= 16
        auxIsFloat = self._auxBits >= 16

        self.debug("Bitcount: color=" +str(self._colorBits) + "; aux="+str(self._auxBits) + "; depth=" + str(self._depthBits))


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
            handle.setMinfilter(Texture.FTLinear)
            handle.setMagfilter(Texture.FTLinear)
            handle.setAnisotropicDegree(0)

            if target == RenderTargetType.Color:
                if colorIsFloat:
                    handle.setComponentType(Texture.TFloat)

                if self._colorBits == 16:
                    handle.setFormat(Texture.FRgba16)
                elif self._colorBits == 32:
                    handle.setFormat(Texture.FRgba32)
            else:
                if colorIsFloat:
                    handle.setComponentType(Texture.TFloat)
                if self._auxBits == 16:
                    handle.setFormat(Texture.FRgba16)
                elif self._auxBits == 32:
                    handle.setFormat(Texture.FRgba32)

            if self._layers > 1:
                handle.setup2dTextureArray(self._layers)

        # set layers for depth texture
        if self._layers > 1 and self.hasTarget(RenderTargetType.Depth):
            self.getTarget(RenderTargetType.Depth).setup2dTextureArray(
                self._layers)

        # Create buffer descriptors
        windowProps = WindowProperties.size(self._width, self._height)
        bufferProps = FrameBufferProperties()

        # Set color and alpha bits
        if self.hasTarget(RenderTargetType.Color):
            bufferProps.setColorBits(self._colorBits * 3)
            bufferProps.setAlphaBits(self._colorBits)

            if colorIsFloat:
                bufferProps.setFloatColor(True)

        # Set aux bits
        if self.hasTarget(RenderTargetType.Aux0) and auxIsFloat:
            bufferProps.setAuxFloat(True)

        # Set depth bits and depth texture format
        if self.hasTarget(RenderTargetType.Depth):
            depthTarget = self.getTarget(RenderTargetType.Depth)

            bufferProps.setDepthBits(self._depthBits)
            bufferProps.setFloatDepth(True)

        # We need no stencil (not supported yet)
        bufferProps.setStencilBits(0)

        numAuxtex = 0

        # Python really needs switch()
        if self.hasTarget(RenderTargetType.Aux3):
            numAuxtex = 4
        elif self.hasTarget(RenderTargetType.Aux2):
            numAuxtex = 3
        elif self.hasTarget(RenderTargetType.Aux1):
            numAuxtex = 2
        elif self.hasTarget(RenderTargetType.Aux0):
            numAuxtex = 1

        # Add aux textures (either 8 or 16 bit)
        if auxIsFloat:
            bufferProps.setAuxHrgba(numAuxtex)
        else:
            bufferProps.setAuxRgba(numAuxtex)

        # Need no multisamples
        bufferProps.setMultisamples(self._multisamples)

        # Create internal graphics output
        self._internalBuffer = Globals.base.graphicsEngine.makeOutput(
            self._win.getPipe(), self._name, 1,
            bufferProps, windowProps,
            GraphicsPipe.BFRefuseWindow | GraphicsPipe.BFResizeable,
            self._win.getGsg(), self._win)

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
        RenderBuffer.numBuffersAllocated += 1
        self._sort = -200 + RenderBuffer.numBuffersAllocated*10

        self.debug("our sort value is", self._sort)

        self._internalBuffer.setSort(self._sort)

        self._internalBuffer.disableClears()
        self._internalBuffer.getDisplayRegion(0).disableClears()

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
