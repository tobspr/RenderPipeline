
from panda3d.core import Vec3, Texture, Shader, LVecBase2i
from DraggableWindow import DraggableWindow
from BetterOnscreenImage import BetterOnscreenImage
from BetterOnscreenText import BetterOnscreenText
from BetterSlider import BetterSlider

class TexturePreview(DraggableWindow):

    """ Small window which provides a preview of a texture """
    def __init__(self):
        DraggableWindow.__init__(self, width=1600, height=900, title="Texture Preview")
        self.currentTex = None
        self._createComponents()
        self._createShaders()

    def present(self, tex):
        """ "Presents" a given texture and shows the window """
        self.currentTex = tex

        # Remove old content
        self._contentNode.removeChildren() 

        w, h = tex.getXSize(), tex.getYSize()
        scaleX = (self.width-40.0) / w
        scaleY = (self.height-110.0) / h
        scaleF = min(scaleX, scaleY)

        image = BetterOnscreenImage(image=tex, parent=self._contentNode, x=20, 
            y=90, w=scaleX*w, h=scaleY*h, anyFilter=False, transparent=False)

        description = ""

        # Image size
        description += "{:d} x {:d} x {:d}".format(tex.getXSize(), tex.getYSize(), tex.getZSize())

        # Image type
        description += ", {:s}, {:s}".format(Texture.formatFormat(tex.getFormat()).upper(), 
            Texture.formatComponentType(tex.getComponentType()).upper())

        descText = BetterOnscreenText(text=description, parent=self._contentNode,
            x=20, y=70, size=18, color=Vec3(0.6, 0.6, 0.6))

        estimatedBytes = tex.estimateTextureMemory()
        sizeDesc = "Estimated memory: {:2.2f} MB".format(estimatedBytes / (1024.0**2) )

        sizeText = BetterOnscreenText(text=sizeDesc, parent=self._contentNode,
            x=self.width-20.0, y=70, size=18, color=Vec3(0.34, 0.564, 0.192), align="right")

        # Assign shaders
        if tex.getZSize() <= 1:
            if tex.getTextureType() == Texture.TTBufferTexture:
                image.setShader(self.displayBufferTexShader)
            else:
                image.setShader(self.display2DTexShader)
        else:

            # Create slice slider
            self.sliceSlider = BetterSlider(parent=self._contentNode, size=250, minValue=0,
                maxValue=tex.getZSize() - 1, callback=self._setSlice, x=450, y=63, value=0)
            self.sliceText = BetterOnscreenText(text="Slice: 5", parent=self._contentNode,
                x=710, y=70, size=18, color=Vec3(0.6, 0.6, 0.6), mayChange=1)

            if tex.getTextureType() == Texture.TT2dTextureArray:
                image.setShader(self.display2DTexArrayShader)
            else:
                image.setShader(self.display3DTexShader)
        image.setShaderInput("viewSize", LVecBase2i(int(scaleX*w), int(scaleY*h) ) )
        image.setShaderInput("slice", 0)
        self.previewImage = image
        self.show()

    
    def _setSlice(self):
        idx = int(self.sliceSlider.getValue())
        self.previewImage.setShaderInput("slice", idx)
        self.sliceText.setText("Slice: " + str(idx))

    
    def _createShaders(self):
        """ Create the shaders to display the textures """
        self.display2DTexShader = Shader.load(Shader.SLGLSL,
            "Shader/GUI/vertex.glsl", "Shader/GUI/display2DTex.glsl")
        self.display3DTexShader = Shader.load(Shader.SLGLSL,
            "Shader/GUI/vertex.glsl", "Shader/GUI/analyze3DTex.glsl")
        self.display2DTexArrayShader = Shader.load(Shader.SLGLSL,
            "Shader/GUI/vertex.glsl", "Shader/GUI/analyze2DTexArray.glsl")
        self.displayBufferTexShader = Shader.load(Shader.SLGLSL,
            "Shader/GUI/vertex.glsl", "Shader/GUI/displayBufferTex.glsl")

    
    def _createComponents(self):
        """ Internal method to init the components """
        DraggableWindow._createComponents(self)
        self._contentNode = self._node.attachNewNode("content")