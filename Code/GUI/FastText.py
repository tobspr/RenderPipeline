
import string

from panda3d.core import DynamicTextFont, Vec4, PTALVecBase4, CardMaker, Vec2
from panda3d.core import Texture, PNMImage, Vec3, NodePath, Shader
from panda3d.core import TransparencyAttrib, PTAFloat, VBase4

from ..Util.DebugObject import DebugObject
from ..Globals import Globals


class FastText(DebugObject):

    """ This class is a fast text renderer which is made for onscreen overlays
    to have minimal to no performance impact """

    _FONT_PAGE_POOL = {}
    _SUPPORTED_GLYPHS = (string.ascii_letters + string.digits +
                         string.punctuation + " ")

    def __init__(self, font="Data/Font/Roboto-Medium.ttf", pixel_size=16, align="left",
                 pos=Vec2(0), color=Vec3(1), outline=Vec4(0, 0, 0, 1), parent=None):
        """ Creates a new text instance with the given font and pixel size """
        DebugObject.__init__(self)
        self._font = font
        self._size = pixel_size
        self._align = align
        self._position = Vec2(pos)
        self._cache_key = self._font + "##" + str(self._size)
        self._parent = Globals.base.aspect2d if parent is None else parent
        self._pta_position = PTALVecBase4.empty_array(100)
        self._pta_offset = PTAFloat.empty_array(1)
        self._pta_uv = PTALVecBase4.empty_array(100)
        self._pta_color = PTALVecBase4.empty_array(2)
        self._pta_color[0] = Vec4(color.x, color.y, color.z, 1.0)
        self._pta_color[1] = Vec4(outline)
        self._text = ""

        if self._cache_key in self._FONT_PAGE_POOL:
            self._font_data = self._FONT_PAGE_POOL[self._cache_key]
        else:
            self.debug("Creating new font cache entry")
            self._extract_font_data()
        self._generate_card()

    def set_color(self, r, g, b):
        """ Sets the text color """
        self._pta_color[0] = Vec4(r, g, b, 1)

    def set_outline_color(self, r=0.0, g=0.0, b=0.0, a=1.0):
        """ Sets the text outline color """
        if isinstance(r, Vec4):
            self._pta_color[1] = r
        else:
            self._pta_color[1] = Vec4(r, g, b, a)

    def set_pos(self, x, y):
        """ Sets the position of the text """
        self._position = Vec2(x, y)

    def set_text(self, text):
        """ Sets the text, up to a number of 100 chars """
        self._text = text[:100]

    def update(self):
        """ Updates the text """
        advance_x = 0.0
        text_scale_x = self._size * 2.0 / float(Globals.base.win.get_y_size())
        # text_scale_y = self._size * 2.0 * 2.0 / float(Globals.base.win.get_y_size())
        text_scale_y = text_scale_x

        for char_pos, char in enumerate(self._text):
            idx = self._SUPPORTED_GLYPHS.index(char)
            uv, pos, advance = self._font_data[2][idx]
            self._pta_uv[char_pos] = uv
            self._pta_position[char_pos] = Vec4(
                self._position.x + (advance_x + pos[0]) * text_scale_x,
                self._position.y + pos[1] * text_scale_y,
                self._position.x + (advance_x + pos[2]) * text_scale_x,
                self._position.y + pos[3] * text_scale_y)
            advance_x += advance

        if self._align == "left":
            self._pta_offset[0] = 0
        elif self._align == "center":
            self._pta_offset[0] = -advance_x * text_scale_x * 0.5
        elif self._align == "right":
            self._pta_offset[0] = -advance_x * text_scale_x

        self._card.set_instance_count(len(self._text))

    def show(self):
        """ Shows the text """
        self._card.show()

    def hide(self):
        """ Hides the text """
        self._card.hide()

    def remove(self):
        """ Removes the text """
        self._card.remove_node()

    def _extract_font_data(self):
        """ Internal method to extract the font atlas """

        # Create a new font instance to generate a font-texture-page
        font_instance = DynamicTextFont(self._font)
        font_instance.set_fg(Vec4(1))

        atlas_size = 1024 if self._size > 30 else 512 
        font_instance.set_page_size(atlas_size, atlas_size)
        font_instance.set_pixels_per_unit(int(self._size * 1.5))
        font_instance.set_texture_margin(int(self._size / 4.0 * 1.5))

        # Register the glyphs, this automatically creates the font-texture page
        glyph_instances = []
        for glyph in self._SUPPORTED_GLYPHS:
            glyph_instances.append(font_instance.get_glyph(ord(glyph)))

        # Extract the page
        page = font_instance.get_page(0)
        page.set_minfilter(Texture.FT_linear)
        page.set_magfilter(Texture.FT_linear)
        page.set_anisotropic_degree(0)

        blurpnm = PNMImage(atlas_size, atlas_size, 4, 256)
        page.store(blurpnm)
        blurpnm.gaussian_filter(self._size / 4)
        page_blurred = Texture("PageBlurred")
        page_blurred.setup_2d_texture(atlas_size, atlas_size,
                                      Texture.T_unsigned_byte, Texture.F_rgba8)
        page_blurred.load(blurpnm)
        page.set_format(Texture.F_red)

        # Extract glyph data
        glyph_data = []

        for index, glyph in enumerate(self._SUPPORTED_GLYPHS):
            glyph_instance = glyph_instances[index]
            dimensions = VBase4()
            texcoords = VBase4()

            # Spaces have no position, skip them
            if glyph == " ":
                glyph_data.append((VBase4(0), VBase4(0), glyph_instance.get_advance()))
                continue

            if not glyph_instance.get_quad(dimensions, texcoords):
                self.warn("Could not get glyph data for: '" + glyph + "'")
                glyph_data.append((VBase4(0), VBase4(0), 0))
                continue

            advance = glyph_instance.get_advance()
            glyph_data.append((texcoords, dimensions, advance))

        self._font_data = [font_instance, page, glyph_data, page_blurred]
        self._glyph_instances = glyph_instances
        self._FONT_PAGE_POOL[self._cache_key] = self._font_data

    def _generate_card(self):
        """ Generates the card used for text rendering """
        c = CardMaker("TextCard")
        c.set_frame(0, 1, 0, 1)
        self._card = NodePath(c.generate())
        self._card.set_shader_input("fontPageTex", self._font_data[1])
        self._card.set_shader_input("fontPageBlurredTex", self._font_data[3])
        self._card.set_shader_input("positionData", self._pta_position)
        self._card.set_shader_input("color", self._pta_color)
        self._card.set_shader_input("uvData", self._pta_uv)
        self._card.set_shader_input("offset", self._pta_offset)
        self._card.set_shader(self._make_font_shader(), 1000)
        self._card.set_attrib(
            TransparencyAttrib.make(TransparencyAttrib.M_alpha), 1000)
        self._card.reparent_to(self._parent)

    def _make_font_shader(self):
        """ Generates the shader used for font rendering """
        return Shader.make(Shader.SLGLSL, """
            #version 150
            uniform mat4 p3d_ModelViewProjectionMatrix;
            in vec4 p3d_Vertex;
            in vec2 p3d_MultiTexCoord0;
            uniform vec4 positionData[100];
            uniform vec4 uvData[100];
            uniform float offset;
            out vec2 texcoord;
            out float glyphidx;

            void main() {
                int instance_offset = int(gl_InstanceID);
                vec4 pos = positionData[instance_offset];
                vec4 uv = uvData[instance_offset];
                texcoord = mix(uv.xy, uv.zw, p3d_MultiTexCoord0);
                /*vec4 finalPos = p3d_Vertex * vec4(pos.z, 0, pos.w, 1.0) +
                                vec4(pos.x + offset, 0, pos.y, 0);*/

                vec4 final_pos = vec4(offset, 0, 0, 1);

                final_pos.x += mix(pos.x, pos.z, p3d_Vertex.x);
                final_pos.z = mix(pos.y, pos.w, p3d_Vertex.z);

                gl_Position = p3d_ModelViewProjectionMatrix * final_pos;
            }
            """, """
            #version 150
            in vec2 texcoord;
            uniform sampler2D fontPageTex;
            uniform sampler2D fontPageBlurredTex;
            uniform vec4 color[2];
            out vec4 result;
            void main() {
                result = texture(fontPageTex, texcoord).xxxx;
                float outlineResult = texture(fontPageBlurredTex, texcoord).x
                                      * 4.0 * (1.0 - result.w);
                result.xyz *= color[0].xyz;
                result = mix(result, color[1] * outlineResult, 1.0 - result.w);
            }
        """)
