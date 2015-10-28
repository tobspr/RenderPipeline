from __future__ import print_function


""" This script generates the normal quantization texture used by the pipeline,
based on a paper by cryengine:

http://advances.realtimerendering.com/s2010/Kaplanyan-CryEngine3(SIGGRAPH%202010%20Advanced%20RealTime%20Rendering%20Course).pdf
Page 39 to 49

It also generates the mipmaps. """


TEXTURE_SIZE = 2048

import sys
sys.path.insert(0, "../../")

from panda3d.core import *
loadPrcFileData("", "textures-power-2 none")
loadPrcFileData("", "window-type offscreen")
loadPrcFileData("", "win-size 100 100")

# loadPrcFileData("", "notify-level-display error")

import direct.directbase.DirectStart
from Code.Globals import Globals
from Code.RenderTarget import RenderTarget
Globals.load(base)

mip = 0

while TEXTURE_SIZE >= 2:
    target = RenderTarget()
    target.set_size(TEXTURE_SIZE, TEXTURE_SIZE)
    target.add_color_texture()
    target.set_color_bits(16)
    target.prepare_offscreen_buffer()

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
            vec3 vQuantizedP = vec3(
                quantize255(vP.x),
                quantize255(vP.y),
                quantize255(vP.z));

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
        const int cmap_size = """ + str(TEXTURE_SIZE) + """;
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
    target.set_shader(Shader.make(Shader.SLGLSL, vertex_shader, fragment_shader))
    base.graphicsEngine.render_frame()
    k = target['color']
    base.graphicsEngine.extractTextureData(k, base.win.get_gsg())
    k.write("NormalQuantizationTex-" + str(mip) + ".png")
    mip += 1
    TEXTURE_SIZE //= 2
    target.delete_buffer()
