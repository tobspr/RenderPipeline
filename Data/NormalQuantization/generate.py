"""

RenderPipeline

Copyright (c) 2014-2015 tobspr <tobias.springer1@gmail.com>

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


""" This script generates the normal quantization texture used by the pipeline,
based on a paper by cryengine:

http://advances.realtimerendering.com/s2010/Kaplanyan-CryEngine3(SIGGRAPH%202010%20Advanced%20RealTime%20Rendering%20Course).pdf
Page 39 to 49

It also generates the mipmaps. """


TEXTURE_SIZE = 1024

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
    target.size = TEXTURE_SIZE
    target.add_color_texture(bits=16)
    target.prepare_offscreen_buffer()

    target_stitch = RenderTarget()
    target_stitch.size = TEXTURE_SIZE
    target_stitch.add_color_texture(bits=16)
    target_stitch.prepare_offscreen_buffer()

    with open("../../Shader/DefaultPostProcess.vert.glsl", "r") as handle:
        vertex_shader = handle.read()

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

    float FindMinimumQuantizationError(vec3 normal)
    {
        normal /= max(abs(normal.x), max(abs(normal.y), abs(normal.z)));
        float fMinError = 100000.0;
        float fOut = 0.2;
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
                fOut = t;
            }
        }
        return fOut;
    }


    void main() {
        const int cmap_size = """ + str(TEXTURE_SIZE) + """;
        vec2 tcoord = gl_FragCoord.xy / vec2(cmap_size);

        vec2 lc = tcoord + vec2(0, 0);
        //vec2 lc = tcoord * 2 - 1;

        vec3 baseDir = vec3(1.0, lc.x, lc.y);
        baseDir = normalize(baseDir);

        float minimumError = FindMinimumQuantizationError(baseDir);

        result.xyz = vec3(minimumError);

        if (minimumError > 1.0) {
            result.xyz = vec3(1, 0, 0);
        }
        if (tcoord.x < tcoord.y) {
            //result.xyz = vec3(0, 0, 1);
        }

        result.w = 1.0;
    }

    """


    stitch_frag = """
    #version 400
    out vec4 result;
    uniform sampler2D SourceTex;
    void main() {
        const int cmap_size = """ + str(TEXTURE_SIZE) + """;
        vec2 texc = gl_FragCoord.xy / vec2(cmap_size);
        vec2 scoord = texc;


        if (false) {
            scoord.x *= scoord.y;
            scoord *= 2.0;

            if (scoord.x > 1.0) scoord.x = 2 - scoord.x;
            if (scoord.y > 1.0) scoord.y = 2 - scoord.y;
        }

        vec3 samp = texture(SourceTex, scoord).xyz;


        result = vec4(samp, 1.0);
    }

    """ 

    target['color'].set_minfilter(SamplerState.FT_nearest)
    target['color'].set_magfilter(SamplerState.FT_nearest)
    target['color'].set_wrap_u(SamplerState.WM_border_color)
    target['color'].set_wrap_v(SamplerState.WM_border_color)
    target['color'].set_border_color(Vec4(1,0, 0, 1))

    target.set_shader(Shader.make(Shader.SLGLSL, vertex_shader, fragment_shader))
    target_stitch.set_shader(Shader.make(Shader.SLGLSL, vertex_shader, stitch_frag))

    target_stitch.set_shader_input("SourceTex", target["color"])

    base.graphicsEngine.render_frame()

    k = target_stitch['color']
    base.graphicsEngine.extractTextureData(k, base.win.get_gsg())

    p = PNMImage()
    k.store(p)
    p.set_num_channels(1)

    p.write("NormalQuantizationTex-" + str(mip) + ".png")
    mip += 1
    TEXTURE_SIZE //= 2


    target.delete_buffer()
    target_stitch.delete_buffer()
