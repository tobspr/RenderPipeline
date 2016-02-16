#version 420

#define USE_MAIN_SCENE_DATA
#pragma include "render_pipeline_base.inc.glsl"

// use the extended gbuffer api
#define USE_GBUFFER_EXTENSIONS 1
#pragma include "includes/gbuffer.inc.glsl"

uniform sampler2D ShadedScene;

out vec4 result;
out vec4 result_predication;

void main() {
    vec2 texcoord = get_texcoord();
    vec3 scene_data = textureLod(ShadedScene, texcoord, 0).xyz;
    vec3 nrm = get_view_normal_approx(texcoord);
    vec3 pos = get_world_pos_at(texcoord);

    // Simple reinhard operator, to get proper edge detection on bright transitions
    scene_data *= 3.0;
    scene_data = scene_data / (1.0 + scene_data);

    // Don't render skybox normals
    if (is_skybox(pos, MainSceneData.camera_pos)) {
      result = vec4(scene_data, 1);
      result_predication = vec4(0.5, 0.5, 1.0, 0);
      return;
    }

    result = vec4(scene_data, 1);
    result_predication = vec4(fma(nrm, vec3(0.5), vec3(0.5)), 0);
}
