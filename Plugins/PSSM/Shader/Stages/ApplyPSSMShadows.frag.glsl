#version 400

#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/PositionReconstruction.inc.glsl"
#pragma include "Includes/GBufferPacking.inc.glsl"

out vec4 result;

uniform sampler2D GBufferDepth;
uniform sampler2D GBuffer0;
uniform sampler2D GBuffer1;
uniform sampler2D GBuffer2;
uniform sampler2D ShadedScene;
uniform sampler2D PSSMShadowAtlas;

uniform float pssm_split_distance;
uniform int pssm_split_count;
uniform mat4 pssm_mvps[10];


vec2 get_split_coord(vec2 local_coord, int split_index) {
    local_coord.x = (local_coord.x + split_index) / float(pssm_split_count);
    return local_coord;
}

void main() {

    ivec2 coord = ivec2(gl_FragCoord.xy);
    float shadow_factor = 0.0;
    vec4 scene_color = texelFetch(ShadedScene, coord, 0);

    // Get the material
    Material m = unpack_material(GBufferDepth, GBuffer0, GBuffer1, GBuffer2);
    vec4 lighting_result = vec4(0);

    // Compute split index
    float depth = texelFetch(GBufferDepth, coord, 0).x;
    float linear_depth = getLinearZFromZ(depth);
    int split = int( log(1 + linear_depth / pssm_split_distance) * pssm_split_count);

    // Compute the shadowing factor
    if (split >= pssm_split_count) {
        shadow_factor = 1.0;
    } else {
        // shadow_factor = Bla;

        mat4 mvp = pssm_mvps[split];

        vec4 projected = mvp * vec4(m.position, 1);
        projected.xyz /= projected.w;
        projected.xyz = fma(projected.xyz, vec3(0.5), vec3(0.5));

        vec2 projected_coord = get_split_coord(projected.xy, split);

        float depth_sample = texture(PSSMShadowAtlas, projected_coord, 0).x;
        float depth_value = step(depth_sample, projected.z - 0.001);

        lighting_result.xyz = vec3(depth_value);


    }

    // Compute the light influence


    result = scene_color + lighting_result;
}