
# Disable ling too long warnings for this file, since we are building shader
# code, so we can make an exception here
# pylint: disable=C0301

from panda3d.core import Shader, Texture
from direct.stdpy.file import isfile, open

from .DebugObject import DebugObject

class DisplayShaderBuilder(object):

    """ Utility class to generate shaders on the fly to display texture previews
    and also buffers """

    @classmethod
    def build(cls, texture, view_width, view_height):
        """ Builds a shader to display <texture> in a view port with the size
        <view_width> * <view_height> """
        view_width, view_height = int(view_width), int(view_height)

        cache_key = "$$PipelineTemp/$$TEXDISPLAY-X{}-Y{}-Z{}-TT{}-CT{}-VW{}-VH{}.frag.glsl".format(
            texture.get_x_size(),
            texture.get_y_size(),
            texture.get_z_size(),
            texture.get_texture_type(),
            texture.get_component_type(),
            view_width,
            view_height)

        # Only regenerate the file when there is no cache entry for it
        if not isfile(cache_key) or True:
            fragment_shader = cls._build_fragment_shader(texture, view_width, view_height)

            with open(cache_key, "w") as handle:
                handle.write(fragment_shader)

        return Shader.load(Shader.SL_GLSL, "Shader/GUI/DefaultGUIShader.vertex.glsl", cache_key)

    @classmethod
    def _build_fragment_shader(cls, texture, view_width, view_height):
        """ Internal method to build a fragment shader displaying the texture """

        sampling_code, sampler_type = cls._generate_sampling_code(texture, view_width, view_height)

        # Build actual shader
        built = """
            #version 400     
            #pragma include "Includes/Configuration.inc.glsl"   
            in vec2 texcoord;
            out vec3 result;
            uniform int mipmap;
            uniform int slice;
            uniform """ + sampler_type + """ p3d_Texture0;
            void main() {
                int view_width = """ + str(view_width) + """;
                int view_height = """ + str(view_height) + """;
                ivec2 display_coord = ivec2(texcoord * vec2(view_width, view_height));
                int int_index = display_coord.x + display_coord.y * view_width;
                """ + sampling_code + """

            }
        """

        # Strip trailing spaces
        built = '\n'.join([i.strip() for i in built.split("\n")])

        return built

    @classmethod
    def _generate_sampling_code(cls, texture, view_width, view_height):
        """ Generates the GLSL code to sample a texture and also returns the
        GLSL sampler type """

        texture_type = texture.get_texture_type()
        comp_type = texture.get_component_type()

        # Useful snippets
        int_coord = "ivec2 int_coord = ivec2(texcoord * textureSize(p3d_Texture0, mipmap).xy);"
        slice_count = "int slice_count = textureSize(p3d_Texture0, mipmap).z;"

        float_types = [Texture.T_float, Texture.T_unsigned_byte]
        int_types = [Texture.T_int, Texture.T_unsigned_short, Texture.T_unsigned_int_24_8]

        # 2D Textures
        if texture_type == Texture.TT_2d_texture:

            if comp_type in float_types:
                return "result = textureLod(p3d_Texture0, texcoord, mipmap).xyz;", "sampler2D"

            elif comp_type in int_types:
                return int_coord + "result = texelFetch(p3d_Texture0, int_coord, mipmap).xyz / 10.0;", "isampler2D"

            else:
                DebugObject.global_warn("DisplayShaderBuilder", "Unkown texture component type:", comp_type)

        # Buffer Textures
        elif texture_type == Texture.TT_buffer_texture:

            range_check = lambda s: "if (int_index < textureSize(p3d_Texture0)) {" + s + "} else { result = vec3(1.0, 0.6, 0.2);};"

            if comp_type in float_types:
                return range_check("result = texelFetch(p3d_Texture0, int_index).xyz;"), "samplerBuffer"

            elif comp_type in int_types:
                return range_check("result = texelFetch(p3d_Texture0, int_index).xyz / 10.0;"), "isamplerBuffer"

        # 3D Textures
        elif texture_type == Texture.TT_3d_texture:

            if comp_type in float_types:
                return slice_count + "result = textureLod(p3d_Texture0, vec3(texcoord, (0.5 + slice) / slice_count), mipmap).xyz;", "sampler3D"

            elif comp_type in int_types:
                return int_coord + "result = texelFetch(p3d_Texture0, ivec3(int_coord, slice), mipmap).xyz / 10.0;", "isampler3D"

        # 2D Texture Array
        elif texture_type == Texture.TT_2d_texture_array:

            if comp_type in float_types:
                return "result = textureLod(p3d_Texture0, vec3(texcoord, slice), mipmap).xyz;", "sampler2DArray"

            elif comp_type in int_types:
                return int_coord + "result = texelFetch(p3d_Texture0, ivec3(int_coord, slice), mipmap).xyz / 10.0;", "isampler2DArray"

        # Cubemap
        elif texture_type == Texture.TT_cube_map:

            code = "vec3 sample_dir = get_cubemap_coordinate(slice, texcoord);\n"
            code += "result = textureLod(p3d_Texture0, sample_dir, mipmap).xyz;"
            return code, "samplerCube"

        return "result = vec3(1, 0, 1);", "sampler2D"
