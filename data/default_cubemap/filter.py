"""

RenderPipeline

Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

from __future__ import print_function, division

import os
from panda3d.core import *
from direct.showbase.ShowBase import ShowBase


cshader = Shader.make_compute(Shader.SL_GLSL, """
#version 430

layout (local_size_x = 8, local_size_y = 8, local_size_z = 6) in;


#define M_PI 3.1415926535897932384626433

vec3 get_transformed_coord(vec2 coord, uint face) {
    float f = 1.0;
    switch (face) {
        case 1: return vec3(-f, coord);
        case 2: return vec3(coord, -f);
        case 0: return vec3(f, -coord.x, coord.y);
        case 3: return vec3(coord.xy * vec2(1,-1), f);
        case 4: return vec3(coord.x, f, coord.y);
        case 5: return vec3(-coord.x, -f, coord.y);
    }
    return vec3(0);
}

// From:
// http://www.trentreed.net/blog/physically-based-shading-and-image-based-lighting/
vec2 hammersley(uint i, uint N)
{
  return vec2(float(i) / float(N), float(bitfieldReverse(i)) * 2.3283064365386963e-10);
}

// From:
// http://www.gamedev.net/topic/655431-ibl-problem-with-consistency-using-ggx-anisotropy/
vec3 importance_sample_ggx(vec2 xi, float roughness)
{
  float r_square = roughness * roughness;
  float phi = 2 * M_PI * xi.x;
  float cos_theta = sqrt((1 - xi.y) / (1 + (r_square*r_square - 1) * xi.y));
  float sin_theta = sqrt(1 - cos_theta * cos_theta);

  vec3 h = vec3(sin_theta * cos(phi), sin_theta * sin(phi), cos_theta);
  return h;
}


// Converts a normalized spherical coordinate (r = 1) to cartesian coordinates
vec3 spherical_to_vector(float theta, float phi) {
    float sin_theta = sin(theta);
    return normalize(vec3(
        sin_theta * cos(phi),
        sin_theta * sin(phi),
        cos(theta)
    ));
}

float brdf_distribution_ggx(float NxH, float roughness) {
    float nxh_sq = NxH * NxH;
    float tan_sq = (1 - nxh_sq) / nxh_sq;
    float f = roughness / (nxh_sq * (roughness * roughness + tan_sq) );
    return f * f / M_PI;
}


// Finds a tangent and bitangent vector based on a given normal
void find_arbitrary_tangent(vec3 normal, out vec3 tangent, out vec3 bitangent) {
    vec3 v0 = abs(normal.z) < (0.99) ? vec3(0, 0, 1) : vec3(0, 1, 0);
    tangent = normalize(cross(v0, normal));
    bitangent = normalize(cross(tangent, normal));
}


vec3 transform_cubemap_coordinates(vec3 coord) {
    //return normalize(coord.xzy * vec3(1,-1,1));
    return normalize(coord.xyz * vec3(1,-1,1));
}

uniform samplerCube SourceTex;
uniform int currentSize;
uniform int currentMip;
uniform layout(rgba16f) imageCube DestTex;

void main() {
    ivec2 coord = ivec2(gl_GlobalInvocationID.xy);
    int face = int(gl_GlobalInvocationID.z);

    vec2 texcoord = vec2(coord + 0.5) / float(currentSize);
    texcoord = texcoord * 2.0 - 1.0;

    vec3 n = get_transformed_coord(texcoord, face);
    n = normalize(n);
    n = transform_cubemap_coordinates(n);
    float roughness = clamp(currentMip / 7.0, 0.001, 1.0);
    roughness *= roughness;

    vec3 tangent, binormal;
    find_arbitrary_tangent(n, tangent, binormal);

    vec4 accum = vec4(0);
    const uint num_samples = 4096;
    for (uint i = 0; i < num_samples; ++i) {
        vec2 xi = hammersley(i, num_samples);
        vec3 r = importance_sample_ggx(xi, roughness);
        vec3 h = normalize(r.x * tangent + r.y * binormal + r.z * n);
        vec3 l = 2.0 * dot(n, h) * h - n;

        float NxL = clamp(dot(n, l), 0.0, 1.0);
        float NxH = clamp(dot(n, h), 0.0, 1.0);

        vec3 sampled = texture(SourceTex, l).rgb;

        // GGX
        float weight = brdf_distribution_ggx(NxH, roughness);
        weight *= NxL;
        weight = clamp(weight, 0.0, 1.0);
        accum += vec4(sampled, 1) * weight;
    }

    accum /= max(0.1, accum.w);


    imageStore(DestTex, ivec3(coord, face), vec4(accum.xyz, 1.0));
}

""")

class Application(ShowBase):
    def __init__(self):
        load_prc_file_data("", """
            textures-power-2 none
            window-type offscreen
            win-size 100 100
            gl-coordinate-system default
            notify-level-display error
        """)

        ShowBase.__init__(self)

        if not os.path.isdir("filtered/"):
            os.makedirs("filtered/")

        cubemap = self.loader.loadCubeMap("#.jpg")
        mipmap, size = -1, cubemap.get_y_size() * 2

        while size > 1:
            size = size // 2
            mipmap += 1
            print("Filtering mipmap", mipmap)

            dest_cubemap = Texture("Dest")
            dest_cubemap.setup_cube_map(size, Texture.T_float, Texture.F_rgba16)

            node = NodePath("")
            node.set_shader(cshader)
            node.set_shader_input("SourceTex", cubemap)
            node.set_shader_input("DestTex", dest_cubemap)
            node.set_shader_input("currentSize", size)
            node.set_shader_input("currentMip", mipmap)
            attr = node.get_attrib(ShaderAttrib)
            self.graphicsEngine.dispatch_compute(
                ( (size + 7) // 8, (size+7) // 8, 1), attr, self.win.get_gsg())

            self.graphicsEngine.extract_texture_data(dest_cubemap, self.win.get_gsg())
            dest_cubemap.write("filtered/{}-#.png".format(mipmap), 0, 0, True, False)

Application()
