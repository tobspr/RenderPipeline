/**
 *
 * RenderPipeline
 *
 * Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 */

#version 430

// Shader used for the environment map

%DEFINES%

#define IS_ENVMAP_SHADER 1

#define USE_TIME_OF_DAY
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/shadows.inc.glsl"
#pragma include "includes/material.struct.glsl"
#pragma include "includes/poisson_disk.inc.glsl"
#pragma include "includes/vertex_output.struct.glsl"

%INCLUDES%
%INOUT%

uniform sampler2D p3d_Texture0;
uniform Panda3DMaterial p3d_Material;

layout(location=0) in VertexOutput vOutput;

#pragma include "includes/forward_shading.inc.glsl"

layout(location=0) out vec4 result;

void main() {

    MaterialBaseInput mInput = get_input_from_p3d(p3d_Material);

    vec3 basecolor = texture(p3d_Texture0, vOutput.texcoord).rgb * mInput.color;

    vec3 ambient = get_forward_ambient(mInput, basecolor);
    vec3 sun_lighting = get_sun_shading(mInput, basecolor);
    vec3 lights = get_forward_light_shading(basecolor);
 
    vec3 combined_lighting = (ambient + lights + sun_lighting) * 0.17;

    result = vec4(combined_lighting, 1);
}
