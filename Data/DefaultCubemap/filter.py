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

from __future__ import print_function

from panda3d.core import PNMImage, load_prc_file_data, Texture, NodePath
from panda3d.core import Shader, ShaderAttrib

import shutil
import os

load_prc_file_data("", "textures-power-2 none")
# load_prc_file_data("", "window-type offscreen")
load_prc_file_data("", "win-size 100 100")
load_prc_file_data("", "notify-level-display error")

import direct.directbase.DirectStart


compute_shader = Shader.make_compute(Shader.SL_GLSL, """
#version 430

layout (local_size_x = 16, local_size_y = 16) in;
uniform writeonly image2D DestTex;
uniform samplerCube SourceCubemap;
uniform int size;
uniform int blurSize;
uniform int effectiveSize;
uniform int faceIndex;


vec3 transform_cubemap_coordinates(vec3 coord) {
    return normalize(coord.xzy * vec3(1,-1,1));
}

vec3 get_transformed_coord(vec2 coord) {
    float f = 1.0;
    if (faceIndex == 1) return vec3(-f, coord);
    if (faceIndex == 2) return vec3(coord, -f);
    if (faceIndex == 0) return vec3(f, -coord.x, coord.y);
    if (faceIndex == 3) return vec3(coord.xy * vec2(1,-1), f);
    if (faceIndex == 4) return vec3(coord.x, f, coord.y);
    if (faceIndex == 5) return vec3(-coord.x, -f, coord.y);
    return vec3(0);
}

void main() {
    ivec2 coord = ivec2(gl_GlobalInvocationID.xy);
    ivec2 local_coord = coord - blurSize;
    vec2 local_texcoord = local_coord / float(size) * 2.0 - 1.0;

    vec3 direction = get_transformed_coord(local_texcoord);
    direction = transform_cubemap_coordinates(direction);
    vec3 sampled = texture(SourceCubemap, direction).xyz;

    imageStore(DestTex, coord, vec4(sampled, 1));
}
""")


def load_nth_face(pth, i):
    return PNMImage(pth.replace("#", str(i)))


def filter_cubemap(orig_pth):

    if not os.path.isdir("Filtered/"):
        os.makedirs("Filtered/")

    # Copy original cubemap
    for i in range(6):
       shutil.copyfile(orig_pth.replace("#", str(i)), "Filtered/0-" + str(i) + ".png")

    mip = 0
    while True:
        print("Filtering mipmap", mip)
        mip += 1
        pth = "Filtered/" + str(mip - 1) + "-#.png"
        dst_pth = "Filtered/" + str(mip) + "-#.png"
        first_img = load_nth_face(pth, 0)
        size = first_img.get_x_size() // 2
        if size < 1:
            break
        blur_size = size * 0.002
        blur_size += mip * 0.85
        blur_size = int(blur_size)
        effective_size = size + 2 * blur_size
        faces = [load_nth_face(pth, i) for i in range(6)]

        cubemap = loader.loadCubeMap(pth)
        node = NodePath("")
        node.set_shader(compute_shader)
        node.set_shader_input("SourceCubemap", cubemap)
        node.set_shader_input("size", size)
        node.set_shader_input("blurSize", blur_size)
        node.set_shader_input("effectiveSize", effective_size)

        final_img = PNMImage(size, size, 3)

        for i in range(6):
            face_dest = dst_pth.replace("#", str(i))
            dst = Texture("Face-" + str(i))
            dst.setup_2d_texture(effective_size, effective_size,
                                 Texture.T_float, Texture.F_rgba16)

            # Execute compute shader
            node.set_shader_input("faceIndex", i)
            node.set_shader_input("DestTex", dst)
            attr = node.get_attrib(ShaderAttrib)
            base.graphicsEngine.dispatch_compute(( (effective_size+15) // 16,
                                                   (effective_size+15) // 16, 1),
                                                 attr, base.win.get_gsg())

            base.graphicsEngine.extract_texture_data(dst, base.win.get_gsg())
            img = PNMImage(effective_size, effective_size, 3)
            dst.store(img)
            img.gaussian_filter(blur_size)
            final_img.copy_sub_image(img, 0, 0, blur_size, blur_size, size, size)
            final_img.write(face_dest)




if __name__ == "__main__":

    # Find out the extension
    files = os.listdir(".")
    num_pngs = 0
    num_jpgs = 0
    for f in files:
        if f.endswith(".png"):
            num_pngs += 1
        elif f.endswith(".jpg"):
            num_jpgs += 1
    extension = "png" if num_pngs >= num_jpgs else "jpg"

    filter_cubemap("#." + extension)
