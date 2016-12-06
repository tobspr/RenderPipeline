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
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"

uniform sampler2D ShadedScene;

uniform GBufferData GBuffer;

layout(location=0) out vec3 result_scattering;
layout(location=1) out vec3 result_sun_color;

#pragma include "scattering_method.inc.glsl"
#pragma include "merge_scattering.inc.glsl"

void main() {
    vec2 texcoord = get_texcoord();

    Material m = unpack_material(GBuffer);
    vec3 view_vector = normalize(m.position - MainSceneData.camera_pos);
    vec3 orig_view_vector = view_vector;

    // Prevent a way too dark horizon by clamping the view vector
    if (is_skybox(m)) {
        view_vector.z = max(view_vector.z, 0.0);
    }

    do_scattering(m.position, view_vector, result_scattering, result_sun_color);

    if (is_skybox(m)) {

        result_scattering = get_merged_scattering(orig_view_vector, result_scattering);
        // Sun disk
        vec3 silhouette_col = vec3(TimeOfDay.scattering.sun_intensity) *
            result_scattering * sky_clip;
        silhouette_col *= 2.0;
        float disk_factor = pow(saturate(dot(orig_view_vector, sun_vector) + 0.000069 * 9), 23.0 * 1e5);
        float upper_disk_factor = smoothstep(0, 1, (orig_view_vector.z + 0.045) * 1.0);
        result_scattering += vec3(1, 0.3, 0.1) * disk_factor * upper_disk_factor *
            silhouette_col * 3.0 * 1e4;

    }
}
