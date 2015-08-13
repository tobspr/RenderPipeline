
# This script generates the mipmap generation shaders

res = 1

for step in xrange(10):

    content = """
#version 400
#extension GL_ARB_shader_image_load_store : enable
#define MIPMAP_SIZE """ + str(res) + """
#pragma include "GI/GenerateMipmap.include"
"""

    with open(str(res) + ".fragment", "w") as handle:
        handle.write(content)

    res *= 2