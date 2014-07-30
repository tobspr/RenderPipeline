from panda3d.core import NodePath, Shader, Vec2, PTAFloat
from panda3d.core import TransparencyAttrib, UnalignedLVecBase4f
from panda3d.core import Texture, Vec3, CardMaker,Filename

from direct.stdpy.file import join
from os.path import dirname, realpath

class FastText:

    """ Very fast text renderer using instanced cards and
    a texture atlas """

    def __init__(self, pos=Vec2(0), rightAligned=False, color=Vec3(0,0,0), size=0.04):

        self._loadCharset()
        self._prepareFontTextures()
        self._makeFontShader()
        self._makeSquare()

        self.data = PTAFloat.empty_array(100)
        self.lastText = ""
        self.size = size
        self.square.setShaderInput("displData", self.data)

        self.rightAligned = rightAligned
        self.pos = pos
        self.posOffset = Vec2(0)
        self.color = color
        self._updateInputs()


    def setPos(self, x, y):
        self.pos = Vec2(x, y)
        self._updateInputs()

    def setRightAligned(self, rightAligned=True):
        self.rightAligned = rightAligned

    def setSize(self, size):
        self.size = size
        self._updateInputs()

    def setText(self, text):
        if text is self.lastText:
            return
        self.lastText = text
        self.square.setInstanceCount(len(text))

        if self.rightAligned:
            self.posOffset = Vec2(-float(len(text))*self.size*0.55, 0)
        else:
            self.posOffset = Vec2(0)

        c = 0
        for char in text:
            index = self.charset.index(char)
            # coordX, coordY = index % 16, int(index / 16)
            # txX, txY = coordX / 16.0, (5 - coordY) / 6.0
            # self.data[c] = UnalignedLVecBase4f(txX, txY, 0, 0)
            self.data[c] = index

            c += 1

        if self.rightAligned:
            self.square.setShaderInput("pos", self.pos + self.posOffset)

    def setColor(self, r, g, b):
        self.color = Vec3(r, g, b)
        self._updateInputs()

    def _prepareFontTextures(self):
        texPath = "Data/Textures/font.png"

        self.fontTex = loader.loadTexture(texPath)
        self.fontTex.setMinfilter(Texture.FTLinear)
        self.fontTex.setMagfilter(Texture.FTLinear)
        self.fontTex.setAnisotropicDegree(16)

    def _loadCharset(self):
        self.charset = """ !"#$%&'()*+,-./"""
        self.charset += """0123456789:;<=>?"""
        self.charset += """@ABCDEFGHIJKLMNO"""
        self.charset += """PQRSTUVWXYZ[\\]^_"""
        self.charset += """`abcdefghijklmno"""
        self.charset += """pqrstuvwxyz{|}~ """

    def _makeFontShader(self):
        self.fontShader = Shader.make(Shader.SLGLSL, """
            #version 400
            uniform mat4 p3d_ModelViewProjectionMatrix;
            in vec4 p3d_Vertex;
            in vec2 p3d_MultiTexCoord0;
            uniform float displData[100];
            out vec2 texcoord;
            uniform vec2 pos;
            uniform vec2 size;

            void main() {
                int rawDispl = int(displData[gl_InstanceID]);
                ivec2 offsetDispl = ivec2( rawDispl % 16, rawDispl / 16);
                vec2 offsetCoordReal = vec2(offsetDispl.x / 16.0, (5.0 - offsetDispl.y) / 6.0);

                texcoord = p3d_MultiTexCoord0 / vec2(16,6) + offsetCoordReal;
                vec4 offset = vec4(gl_InstanceID*size.x*0.55 , 0, 0, 0) + vec4(pos.x, 0, pos.y, 0);
                vec4 finalPos = p3d_Vertex * vec4(size.x, size.x, size.x, 1.0) + offset;
                gl_Position = p3d_ModelViewProjectionMatrix * finalPos;
            }
            """, """
            #version 400
            in vec2 texcoord;
            uniform sampler2D font;
            uniform vec3 color;
            void main() {
                float textFactor = texture(font, texcoord).x;
                gl_FragColor = vec4(color, textFactor);

            } 
        """)

    def _updateInputs(self):
        self.square.setShaderInput("pos", self.pos + self.posOffset)
        self.square.setShaderInput("size", Vec2(self.size))
        self.square.setShaderInput("color", self.color)

    def _makeSquare(self):
        c = CardMaker("square")
        c.setFrame(-0.5, 0.5, -0.5, 0.5)
        self.square = NodePath(c.generate())
        self.square.setShaderInput("font", self.fontTex)
        self.square.setShader(self.fontShader)
        self.square.setAttrib(
            TransparencyAttrib.make(TransparencyAttrib.MAlpha), 100)
        self.square.reparentTo(aspect2d)
        return self.square
