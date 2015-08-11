

import sys
sys.path.insert(0, "../../")
from panda3d.core import *

loadPrcFileData("", "textures-power-2 none")

import os

import direct.directbase.DirectStart
from Code.Globals import Globals


Globals.load(base)
from Code.RenderTarget import RenderTarget


import shutil

sz = 2048

target = RenderTarget()
target.setSize(sz, sz)
target.addColorTexture()
target.setColorBits(16)
target.prepareOffscreenBuffer()

vertex_shader = """
#version 400

uniform mat4 p3d_ModelViewProjectionMatrix;

in vec4 p3d_Vertex;
out vec2 texcoord;

void main() {
    gl_Position = vec4(p3d_Vertex.x, p3d_Vertex.z, 0, 1);
    texcoord = sign(p3d_Vertex.xz * 0.5 + 0.5);
}
"""

fragment_shader = """
#version 400

out vec4 result;

float quantize255(float c)
{
    float w = clamp(c * 0.5 + 0.5, 0.0, 1.0);
    float r = round(w * 255.0);
    float v = r / 255.0 * 2.0 - 1.0;
    return v;
}

vec3 FindMinimumQuantizationError(vec3 normal)
{
    normal /= max(abs(normal.x), max(abs(normal.y), abs(normal.z)));
    float fMinError = 100000.0;
    vec3 fOut = normal;
    for(float nStep = 1.5;nStep <= 127.5;++nStep)
    {
        float t = nStep / 127.5;

        // compute the probe
        vec3 vP = normal * t;

        // quantize the probe
        vec3 vQuantizedP = vec3(quantize255(vP.x), quantize255(vP.y), quantize255(vP.z));

        // error computation for the probe
        vec3 vDiff = (vQuantizedP - vP) / t;
        float fError = max(abs(vDiff.x), max(abs(vDiff.y), abs(vDiff.z)));

        // find the minimum
        if(fError < fMinError)
        {
            fMinError = fError;
            fOut = vec3(t);
        }
    }
    return fOut;
}


void main() {
    const int cmap_size = """ + str(sz) + """;
    ivec2 coord = ivec2(gl_FragCoord.xy + 0.5);
    vec2 lc = coord / float(cmap_size);
    lc.y = 1.0 - lc.y;
    lc.y *= lc.x;

    vec3 baseDir = normalize(vec3(1, lc.x, lc.y));
   
    vec3 minimumError = FindMinimumQuantizationError(baseDir);

    float res = minimumError.x;

    res /= max(abs(baseDir.x), max(abs(baseDir.y), abs(baseDir.z)));

    result.xyz = vec3(res);
    result.w = 1.0;


}


"""


target.setShader(Shader.make(Shader.SLGLSL, vertex_shader, fragment_shader))

base.graphicsEngine.renderFrame()

k = target.getColorTexture()
base.graphicsEngine.extractTextureData(k, base.win.getGsg())
k.write("NormalQuantizationTex.png")

