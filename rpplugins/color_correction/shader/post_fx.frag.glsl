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

#version 420

#define USE_MAIN_SCENE_DATA
#define USE_TIME_OF_DAY
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/transforms.inc.glsl"
#pragma include "includes/noise.inc.glsl"

#pragma include "chromatic_aberration.inc.glsl"

uniform sampler2D ShadedScene;

out vec4 result;


void main() {

    vec2 texcoord = get_texcoord();

    #if !DEBUG_MODE

        // Physically correct vignette, using the cos4 law.
        // Get the angle between the camera direction and the view direction
        vec3 material_dir = normalize(MainSceneData.camera_pos - calculate_surface_pos(1, texcoord));
        vec3 cam_dir = normalize(MainSceneData.camera_pos - calculate_surface_pos(1, vec2(0.5)));

        // According to the cos4 law, the brightness at angle alpha is cos^4(alpha).
        // Since dot() returns the cosine, we can just pow it to get a physically
        // correct vignette.
        float cos_angle = dot(cam_dir, material_dir);
        float vignette = pow(cos_angle, 4.0);

        // Chromatic abberation
        #if GET_SETTING(color_correction, use_chromatic_aberration)
            vec3 scene_color = do_chromatic_aberration(ShadedScene, texcoord, 1-vignette);
        #else
            vec3 scene_color = textureLod(ShadedScene, texcoord, 0).xyz;
        #endif

        // Compute film grain
        float film_grain = grain(MainSceneData.frame_time);
        vec3 blended_color = blend_soft_light(scene_color, vec3(film_grain));

        // Blend film grain
        float grain_factor = GET_SETTING(color_correction, film_grain_strength);
        scene_color = mix(scene_color, blended_color, grain_factor);

        // Apply the vignette based on the vignette strength
        scene_color *= mix(1.0, vignette, GET_SETTING(color_correction, vignette_strength));

    #else
        vec3 scene_color = textureLod(ShadedScene, texcoord, 0).xyz;
    #endif // !DEBUG_MODE

    result = vec4(scene_color, 1);
}
