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
#define USE_GBUFFER_EXTENSIONS
#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/gbuffer.inc.glsl"

uniform samplerCubeArray CubemapStorage;

out vec4 result;

void main() {

    vec2 texcoord = get_texcoord();
    Material m = unpack_material(GBuffer, texcoord);

    if (is_skybox(m, MainSceneData.camera_pos)) {
        result = vec4(0);
        return;
    }

    vec3 view_vector = normalize(MainSceneData.camera_pos - m.position);

    // TODO: Do for every cubemap
    vec3 cubemap_pos = vec3(0, 0, 2);
    int cubemap_index = 0;
    vec3 reflected_dir = reflect(-view_vector, m.normal);

    vec3 cube_to_obj = normalize(m.position - cubemap_pos) * 0.1;
    vec3 parallax = cube_to_obj;

    vec4 cubemap_result = texture(CubemapStorage, vec4(reflected_dir + parallax, cubemap_index)) * 1.0;



    result = cubemap_result;
}
