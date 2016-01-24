#version 400

#define USE_MAIN_SCENE_DATA
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/GBuffer.inc.glsl"

uniform vec3 voxelGridPosition;
uniform float voxelGridSize;
uniform int voxelGridResolution;

uniform sampler3D SceneVoxels;
uniform sampler2D ShadedScene;

uniform samplerCube ScatteringIBLSpecular;

uniform GBufferData GBuffer;
out vec4 result;



void main() {

    Material m = unpack_material(GBuffer);

    // Get voxel space coordinate
    vec3 voxel_coord = (m.position - voxelGridPosition) / GET_SETTING(VXGI, grid_ws_size);
    voxel_coord = fma(voxel_coord, vec3(0.5), vec3(0.5));

    // Get view vector
    vec3 view_vector = normalize(MainSceneData.camera_pos - m.position);
    vec3 reflected_dir = reflect(-view_vector, m.normal);


    if (voxel_coord.x < 0.0 || voxel_coord.y < 0.0 || voxel_coord.z < 0.0 ||
        voxel_coord.x > 1.0 || voxel_coord.y > 1.0 || voxel_coord.z > 1.0)
    {
        result = texture(ScatteringIBLSpecular, reflected_dir);
        return;
    }

    vec3 specular_gi = vec3(0);


    // Trace specular cone
    vec3 start_pos = voxel_coord;
    vec3 end_pos = start_pos + reflected_dir * 0.5;
    vec3 current_pos = start_pos + reflected_dir * 2.0 / GET_SETTING(VXGI, grid_resolution);

    const int num_steps = 256;
    vec3 trace_step = (end_pos - start_pos) / num_steps;
    vec4 accum = vec4(0.0);
    for (int i = 0; i < num_steps; ++i) {
        vec4 sampled = textureLod(SceneVoxels, current_pos, 0);
        accum += sampled * (1.0 - accum.w);
        current_pos += trace_step;
    }

    accum.xyz = accum.xyz / (1 - accum.xyz);
    // accum.xyz *= 0.1;

    accum.xyz += texture(ScatteringIBLSpecular, reflected_dir).xyz * (1-accum.w);

    result = vec4(accum.xyz, 1.0);

}
