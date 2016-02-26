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

#version 400

#define USE_MAIN_SCENE_DATA
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"
#pragma include "includes/poisson_disk.inc.glsl"
#pragma include "vxgi.inc.glsl"

flat in int instance;

uniform sampler2D ShadedScene;
uniform sampler2D Noise4x4;
uniform GBufferData GBuffer;
out vec4 result;

void main() {

    int quad_x = instance % 2;
    int quad_y = instance / 2;

    // Get texture coordinate
    ivec2 coord = (ivec2(gl_FragCoord.xy) * 4) % SCREEN_SIZE_INT;
    coord += ivec2(quad_x, quad_y) * 2;
    vec2 texcoord = (coord + 0.5) / SCREEN_SIZE;

    // vec3 noise_vec = fma(texelFetch(Noise4x4, ivec2(quad_x, quad_y), 0).xyz, vec3(2), vec3(-1));
    vec3 noise_vec = fma(texelFetch(Noise4x4, (coord/2 + ivec2(quad_x, quad_y)) % 4, 0).xyz, vec3(2), vec3(-1));
    // vec3 noise_vec = vec3(0, 0, 0);


    // Get material data
    Material m = unpack_material(GBuffer, texcoord);
    vec3 voxel_coord = worldspace_to_voxelspace(m.position);

    // Get view vector
    vec3 view_vector = normalize(MainSceneData.camera_pos - m.position);
    vec3 reflected_dir = reflect(-view_vector, m.normal);

    if (out_of_unit_box(voxel_coord))
    {
        result = texture(ScatteringIBLDiffuse, m.normal);
        return;
    }

    // Trace diffuse cones
    vec4 accum = vec4(0);

    for (int i = 0; i < 32; ++i) {
        vec3 direction = poisson_disk_3D_32[i];
        direction = mix(direction, noise_vec, 0.3);
        direction = normalize(direction);
        direction = face_forward(direction, m.normal);

        float weight = dot(m.normal, direction); // Guaranteed to be > 0
        weight = 1.0;
        vec4 cone = trace_cone(
            voxel_coord,
            m.normal,
            direction,
            GET_SETTING(vxgi, diffuse_cone_steps),
            false,
            0.1);
        accum.xyz += cone.xyz * weight;
        accum.w += weight;
    }
    accum /= accum.w;
    result = accum;
}
