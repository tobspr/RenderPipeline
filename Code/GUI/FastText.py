
import string

from panda3d.core import DynamicTextFont, Vec4, PTALVecBase4, CardMaker, Vec2
from panda3d.core import Texture, PNMImage, Vec3

from ..Util.DebugObject import DebugObject
from ..Util.FunctionDecorators import protected
from ..Globals import Globals

class FastText(DebugObject):

    """ This class is a fast text renderer which is made for onscreen overlays
    to have minimal to no performance impact """

    fontPagePool = {}
    supportedGlyphs = string.ascii_letters + string.digits + string.punctuation + " "

    def __init__(self, font="Data/Font/SourceSansPro-Bold.otf", pixelSize=16, pos=Vec2(0), color=Vec3(1), outline=Vec4(0, 0, 0, 1)):
        """ Creates a new text instance with the given font and pixel size """
        DebugObject.__init__(self, FastText)
        self.font = font
        self.size = pixelSize
        self.position = Vec2(pos)
        self.cacheKey = self.font + "##" + str(self.size)
        self.parent = Globals.base.aspect2d
        self.ptaPosition = PTALVecBase4.emptyArray(100)
        self.ptaUV = PTALVecBase4.emptyArray(100)
        self.ptaColor = PTALVecBase4.emptyArray(2)
        self.ptaColor[0] = Vec4(color.x, color.y, color.z, 1.0)
        self.ptaColor[1] = Vec4(outline)
        self.text = ""

        if self.cacheKey in self.fontPagePool:
            self.fontData = self.fontPagePool[self.cacheKey]
        else:
            self.debug("Creating new font cache entry")
            self._extractFontData()

        self._generateCard()

    def setColor(self, r, g, b):
        """ Sets the text color """
        self.ptaColor[0] = Vec4(r, g, b, 1)

    def setOutlineColor(self, r=0.0, g=0.0, b=0.0, a=1.0):
        """ Sets the text outline color """
        if isinstance(r, Vec4):
            self.ptaColor[1] = r
        else:
            self.ptaColor[1] = Vec4(r, g, b, a)

    def setPos(self, x, y):
        """ Sets the position of the text """
        self.position = Vec2(x, y)

    def setText(self, text):
        """ Sets the text, up to a number of 100 chars """
        self.text = text[:100]

    def update(self):
        """ Updates the text """
        advanceX = 0.0
        textScaleX = self.size * 2.0 / float(Globals.base.win.getYSize())
        textScaleY = textScaleX
        
        for charPos, char in enumerate(self.text):
            idx = self.supportedGlyphs.index(char)
            uvBegin, uvSize, posBegin, posSize, advance = self.fontData[2][idx]

            self.ptaUV[charPos] = Vec4(uvBegin[0], uvBegin[1], uvSize[0], uvSize[1])
            self.ptaPosition[charPos] = Vec4( 
                self.position.x + (advanceX + posBegin[0])*textScaleX,
                self.position.y + posBegin[1] * textScaleY,
                posSize[0] * textScaleX,
                posSize[1] * textScaleY)
            advanceX += advance

        self.card.setInstanceCount(len(self.text))

    def show(self):
        """ Shows the text """
        self.card.show()

    def hide(self):
        """ Hides the text """
        self.card.hide()

    def remove(self):
         """ Removes the text """
         self.card.removeNode()


    
    def _extractFontData(self):
        """ Internal method to extract the font atlas """

        # Create a new font instance to generate a font-texture-page
        fontInstance = DynamicTextFont(self.font)

        atlasSize = 1024 if i > 30 else 512 
        fontInstance.setPageSize(atlasSize, atlasSize)
        fontInstance.setPixelsPerUnit(int(self.size * 1.5))
        fontInstance.setTextureMargin(int(self.size / 4.0 * 1.5))
        
        # Register the glyphs, this automatically creates the font-texture page
        for glyph in self.supportedGlyphs:
            fontInstance.getGlyph(ord(glyph))

        # Extract the page
        page = fontInstance.getPage(0)
        page.setMinfilter(Texture.FTLinear)
        page.setMagfilter(Texture.FTLinear)
        page.setAnisotropicDegree(0)

        blurpnm = PNMImage(atlasSize, atlasSize, 4, 256)
        page.store(blurpnm)
        blurpnm.gaussianFilter(self.size / 4)
        pageBlurred = Texture("PageBlurred")
        pageBlurred.setup2dTexture(atlasSize, atlasSize, Texture.TUnsignedByte, Texture.FRgba8)
        pageBlurred.load(blurpnm)

        # Extract glyph data
        glyphData = []

        for glyph in self.supportedGlyphs:
            glyphInstance = fontInstance.getGlyph(ord(glyph))
            uvBegin = glyphInstance.getUvLeft(), glyphInstance.getUvBottom()
            uvSize = glyphInstance.getUvRight() - uvBegin[0], glyphInstance.getUvTop() - uvBegin[1]

            posBegin = glyphInstance.getLeft(), glyphInstance.getBottom()
            posSize = glyphInstance.getRight() - posBegin[0], glyphInstance.getTop() - posBegin[1]

            advance = glyphInstance.getAdvance()

            glyphData.append( (uvBegin, uvSize, posBegin, posSize, advance) )

        self.fontData = [fontInstance, page, glyphData, pageBlurred]
        self.fontPagePool[self.cacheKey] = self.fontData

    
    def _generateCard(self):
        """ Generates the card used for text rendering """
        c = CardMaker("TextCard")
        c.setFrame(0, 1, 0, 1)
        self.card = NodePath(c.generate())
        self.card.setShaderInput("fontPageTex", self.fontData[1])
        self.card.setShaderInput("fontPageBlurredTex", self.fontData[3])
        self.card.setShaderInput("positionData", self.ptaPosition)
        self.card.setShaderInput("color", self.ptaColor)
        self.card.setShaderInput("uvData", self.ptaUV)
        self.card.setShader(self._makeFontShader(), 1000)
        self.card.setAttrib(
            TransparencyAttrib.make(TransparencyAttrib.MAlpha), 1000)
        self.card.reparentTo(self.parent)

    
    def _makeFontShader(self):
        """ Generates the shader used for font rendering """
        return Shader.make(Shader.SLGLSL, """
            #version 150
            uniform mat4 p3d_ModelViewProjectionMatrix;
            in vec4 p3d_Vertex;
            in vec2 p3d_MultiTexCoord0;
            uniform vec4 positionData[100];
            uniform vec4 uvData[100];
            out vec2 texcoord;

            void main() {
                int offset = int(gl_InstanceID);
                vec4 pos = positionData[offset];
                vec4 uv = uvData[offset];
                texcoord = uv.xy + p3d_MultiTexCoord0 * uv.zw;
                vec4 finalPos = p3d_Vertex * vec4(pos.z, 0, pos.w, 1.0) + vec4(pos.x, 0, pos.y, 0);
                gl_Position = p3d_ModelViewProjectionMatrix * finalPos;
            }
            """, """
            #version 150
            in vec2 texcoord;
            uniform sampler2D fontPageTex;
            uniform sampler2D fontPageBlurredTex;
            uniform vec4 color[2];
            out vec4 result;
            void main() {
                result = texture(fontPageTex, texcoord);
                float outlineResult = texture(fontPageBlurredTex, texcoord).x * 4.0 * (1.0 - result.w);
                result.xyz = (1.0 - result.xyz ) * color[0].xyz;
                result = mix(result, color[1] * outlineResult, 1.0 - result.w);
            }
        """)


if __name__ == "__main__":

    from panda3d.core import *
    loadPrcFileData("", "win-size 1920 1080")
    loadPrcFileData("", "show-frame-rate-meter #t")
    loadPrcFileData("", "sync-video #f")
    import direct.directbase.DirectStart
    import time

    posY = 0.9

    for i in xrange(8, 64, 3):
        f = FastText(font="../../Data/Font/DebugFont.ttf", pixelSize=i)
        f.setText("Hello World!")
        f.setPos(-1.0, posY)
        f.setOutlineColor(0, 0, 0, 0)
        f.update()

        posY -= (i*2+10.0) / float(Globals.base.win.getYSize())

    run()