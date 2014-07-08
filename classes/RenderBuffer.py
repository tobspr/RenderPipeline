
from panda3d.core import GraphicsOutput, Texture, WindowProperties
from panda3d.core import FrameBufferProperties, GraphicsPipe, Vec2
from RenderTargetType import RenderTargetType
from DebugObject import DebugObject

# Wrapper arround GraphicsBuffer
class RenderBuffer(DebugObject):

    numBuffersAllocated = 0

    def __init__(self, name="RB"):
        DebugObject.__init__(self, "RenderBuffer")
        self._name = name
        self._width = 0
        self._height = 0
        self._colorBits = 8
        self._auxBits = 8
        self._bindMode = GraphicsOutput.RTMBindOrCopy
        self._depthBits = 24

        self._internalBuffer = None
        self._targets = {}
        self._win = None
        self._layers = 0

        self.mute()

    # How much layers to render
    def setLayers(self, layers):
        self._layers = layers

    # Name of this buffer
    def setName(self, name):
        self._name = name

    # Sets the target window for this buffer
    def setWindow(self, window):
        self._win = window

    # Set buffer size
    def setSize(self, width, height):
        self._width = width
        self._height = height

        if self._internalBuffer is not None:
            self._internalBuffer.setSize(width, height)

    # Returns the buffer size
    def getSize(self):
        return Vec2(self._width, self._height)

    # Sets the required color bits
    def setColorBits(self, colorBits):
        self._colorBits = colorBits

    # Sets the required aux bits
    def setAuxBits(self, auxBits):
        self._auxBits = auxBits

    # Adds a render target 
    def addTarget(self, target):
        if target in self._targets:
            print "You cannot add another target of type",target
            return

        self._targets[target] = Texture("RenderTargetTex-"+target)

    # Either BindOrCopy or BindLayered
    def setBindMode(self, bindMode):
        self._bindMode = bindMode

    # Depth Bits: 8, 16, 24 or 32
    def setDepthBits(self, depthBits):
        self._depthBits = depthBits

    # Returns a handle to the internal buffer object
    def getInternalBuffer(self):
        return self._internalBuffer

    # Check if the target is assigned
    def hasTarget(self, target):
        return target in self._targets

    # Returns a handle to the target (Texture)
    def getTarget(self, target):
        return self._targets[target]

    # Attempts to create this buffer
    def create(self):

        is16bit = self._colorBits >= 16
        auxIs16Bit = self._auxBits >= 16

        self.debug("Creating buffer with",self._colorBits,"color bits and",self._auxBits,"aux bits")


        # set wrap modes for color + auxtextures
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

            # No longer needed?
            if is16bit:
                handle.setComponentType(Texture.TFloat)
                handle.setFormat(Texture.FRgba16)



            if self._layers > 1:
                self.debug("Setup layer count:",self._layers)
                handle.setup2dTextureArray(self._layers)

        # set layers for depth texture
        if self._layers > 1:
            self.debug("Setup depth-layer count:",self._layers)
            self.getTarget(RenderTargetType.Depth).setup2dTextureArray(self._layers)


        if self._colorBits == 32:
            self.getTarget(RenderTargetType.Color).setFormat(Texture.FRgba32)

        # Create buffer descriptors
        windowProps = WindowProperties.size(self._width, self._height)
        bufferProps = FrameBufferProperties()

        # Set color and alpha bits 
        if self.hasTarget(RenderTargetType.Color):
            bufferProps.setColorBits(self._colorBits * 3)
            bufferProps.setAlphaBits(self._colorBits)

            if is16bit:
                bufferProps.setFloatColor(True)

        # Set aux bits
        if self.hasTarget(RenderTargetType.Aux0) and auxIs16Bit:
            bufferProps.setAuxFloat(True)


        # Set depth bits and depth texture format
        if self.hasTarget(RenderTargetType.Depth):
            depthTarget = self.getTarget(RenderTargetType.Depth)

            bufferProps.setDepthBits(self._depthBits)
            bufferProps.setFloatDepth(True)

        # We need no stencil
        bufferProps.setStencilBits(0)

   

        numAuxtex = 0

        # Python really needs switch()
        if self.hasTarget(RenderTargetType.Aux3):    numAuxtex = 4
        elif self.hasTarget(RenderTargetType.Aux2):  numAuxtex = 3
        elif self.hasTarget(RenderTargetType.Aux1):  numAuxtex = 2
        elif self.hasTarget(RenderTargetType.Aux0):  numAuxtex = 1

        # Add aux textures (either 8 or 16 bit)
        if auxIs16Bit:
            bufferProps.setAuxHrgba(numAuxtex)
        else:
            bufferProps.setAuxRgba(numAuxtex)

        # Need no multisamples
        bufferProps.setMultisamples(0)
        

        # Create internal graphics output
        self._internalBuffer = base.graphicsEngine.makeOutput(
            self._win.getPipe(), self._name, 1,
            bufferProps, windowProps, 
            GraphicsPipe.BFRefuseWindow | GraphicsPipe.BFResizeable,
            self._win.getGsg(), self._win)

        if self._internalBuffer is None:
            print "Failed to create buffer :("
            return False

        # Add render targets
        if self.hasTarget(RenderTargetType.Depth):
            self._internalBuffer.addRenderTexture(
                self.getTarget(RenderTargetType.Depth), self._bindMode, GraphicsOutput.RTPDepth)

        if self.hasTarget(RenderTargetType.Color):
            self._internalBuffer.addRenderTexture(
                self.getTarget(RenderTargetType.Color), self._bindMode, GraphicsOutput.RTPColor)

        # We can't use a for because panda uses enums .. 

        if self.hasTarget(RenderTargetType.Aux0):
            self._internalBuffer.addRenderTexture(
                self.getTarget(RenderTargetType.Aux0), self._bindMode, 
                GraphicsOutput.RTPAuxHrgba0 if auxIs16Bit else GraphicsOutput.RTPAuxRgba0)

        if self.hasTarget(RenderTargetType.Aux1):
            self._internalBuffer.addRenderTexture(
                self.getTarget(RenderTargetType.Aux1), self._bindMode, 
                GraphicsOutput.RTPAuxHrgba1 if auxIs16Bit else GraphicsOutput.RTPAuxRgba1)

        if self.hasTarget(RenderTargetType.Aux2):
            self._internalBuffer.addRenderTexture(
                self.getTarget(RenderTargetType.Aux2), self._bindMode, 
                GraphicsOutput.RTPAuxHrgba2 if auxIs16Bit else GraphicsOutput.RTPAuxRgba2)

        if self.hasTarget(RenderTargetType.Aux3):
            self._internalBuffer.addRenderTexture(
                self.getTarget(RenderTargetType.Aux3), self._bindMode, 
                GraphicsOutput.RTPAuxHrgba3 if auxIs16Bit else GraphicsOutput.RTPAuxRgba3)


        RenderBuffer.numBuffersAllocated += 1

        self._internalBuffer.setSort(-20 + RenderBuffer.numBuffersAllocated)
        self._internalBuffer.disableClears()
        self._internalBuffer.getDisplayRegion(0).disableClears()

        self._internalBuffer.setClearStencilActive(False)

        if self.hasTarget(RenderTargetType.Depth):
            depthTarget = self.getTarget(RenderTargetType.Depth)

            self.debug("Preparing depth texture for",self._depthBits,"bits")

            # No longer needed??
            if self._depthBits == 24:
                # depthTarget.setComponentType(Texture.TFloat)
                depthTarget.setFormat(Texture.FDepthComponent24)
            elif self._depthBits == 32:
                # depthTarget.setComponentType(Texture.TFloat)
                depthTarget.setFormat(Texture.FDepthComponent32)

        return True