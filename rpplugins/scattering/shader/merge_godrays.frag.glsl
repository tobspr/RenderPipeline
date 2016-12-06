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

#define USE_TIME_OF_DAY 1
#define USE_GBUFFER_EXTENSIONS

#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"
#pragma include "includes/color_spaces.inc.glsl"

uniform sampler2D ShadedScene;
uniform sampler2D GodrayTex;

out vec4 result;

void main() {

    vec2 texcoord = get_texcoord();
    vec4 scene_result = textureLod(ShadedScene, texcoord, 0);

    float godray_factor = textureLod(GodrayTex, texcoord, 0).x;
    godray_factor *= godray_factor * 5;


    vec3 godray_color = get_sun_color() * godray_factor * 0.09 * GET_SETTING(scattering, godrays_strength);
    #if HAVE_PLUGIN(color_correction)
        godray_color *= 5.5;
    #endif
    godray_color *= godray_color * get_sun_color() * 0.1;

    scene_result.xyz = scene_result.xyz * (1 - saturate(0.0 * godray_factor)) + godray_color;
    result = scene_result;
}
