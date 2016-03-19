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

#define USE_MAIN_SCENE_DATA
#define USE_TIME_OF_DAY
#pragma include "render_pipeline_base.inc.glsl"


uniform writeonly imageCube RESTRICT DestCubemap;
uniform sampler2D DefaultSkydome;

#pragma include "scattering_method.inc.glsl"

void main() {

    // Get cubemap coordinate
    int texsize = imageSize(DestCubemap).x;
    ivec2 coord = ivec2(gl_FragCoord.xy);

    // Get cubemap direction
    ivec2 clamped_coord; int face;
    vec3 direction = texcoord_to_cubemap(texsize, coord, clamped_coord, face);

    // Store horizon
    float horizon = direction.z;
    direction.z = abs(direction.z);
    float fog_factor = 0.0;

    // Get inscattered light
    vec3 inscattered_light = DoScattering(direction * 1e10, direction, fog_factor)
                             * TimeOfDay.scattering.sun_intensity
                             * TimeOfDay.scattering.sun_color * 0.01;

    if (horizon > 0.0) {
        // Clouds
        vec3 view_vector = direction;
        vec3 cloud_color = textureLod(DefaultSkydome, get_skydome_coord(view_vector), 0).xyz;
        cloud_color = cloud_color * vec3(1.0, 1, 0.9) * vec3(0.8, 0.7, 0.8524);
        cloud_color *= saturate(6.0 * (0.05 + view_vector.z));
        inscattered_light *= 0.0 + 1.2 * (0.3 + 0.6 * cloud_color);

    } else {
        // Ground reflectance
        inscattered_light *= saturate(1+0.9*horizon) * 0.05;
        inscattered_light += saturate(-horizon + 0.2) * 1.7 * TimeOfDay.scattering.sun_intensity;
    }

    imageStore(DestCubemap, ivec3(clamped_coord, face), vec4(inscattered_light, 1.0) );
}
