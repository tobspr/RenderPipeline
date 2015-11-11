#version 400

#pragma optionNV (unroll all)

#pragma include "Includes/Configuration.inc.glsl"

in vec2 texcoord;
out vec4 result;

uniform sampler2D DepthSource;

void main() {


    const float tangent_bias = 0.15;
    const float sampling_radius = 30.0;

    vec2 sample_coord = texcoord;
    ivec2 coord = ivec2(gl_FragCoord).xy;

    vec2 sample_radius = vec2(50.0) / vec2(WINDOW_WIDTH, WINDOW_HEIGHT);

    float averaged_samples = 0.0;

    const int num_radii = 32;
    const int num_raymarch = 2;

    vec4 mid_data = texelFetch(DepthSource, coord, 0);
    vec3 vp_dx = texelFetch(DepthSource, coord + ivec2(1, 0), 0).xyz;
    vec3 vp_dy = texelFetch(DepthSource, coord + ivec2(0, 1), 0).xyz;

    float mid_depth = mid_data.w;
    vec3 mid_vp = mid_data.xyz;

    // Extract view normal from view position
    vec3 mid_nrm = normalize(cross(mid_vp - vp_dx, mid_vp - vp_dy));


    // Sample in spherical coordinates
    for (int i = 0; i < num_radii; ++i) {

        // Compute the angle, and the vector pointing into that direction
        float phi = (i / float(num_radii)) * TWO_PI;
        vec2 sample_dir = vec2(cos(phi), sin(phi));

        // TODO: Get that acos out of there
        float tangent_angle = acos(dot(vec3(sample_dir, 0), mid_nrm)) - HALF_PI + tangent_bias;
        float horizon_angle = tangent_angle;

        // Store last difference
        vec3 last_diff = vec3(0);

        for (int k = 0; k < num_raymarch; ++k) {
            float theta = (k + 1) / float(num_raymarch);
            vec2 offcoord = texcoord + sample_dir * theta * sample_radius;

            vec4 data = textureLod(DepthSource, offcoord, 0);
            vec3 vp_diff = data.xyz - mid_vp;

            // if (length(vp_diff) < sampling_radius) {
                last_diff = vp_diff;
                float elevation = atan(vp_diff.z / length(vp_diff.xy));
                horizon_angle = max(horizon_angle, elevation);
            // }
        }

        // Compute attenuation, use difference of ray end for that
        float attenuation = 1.0 / (1 + length(last_diff));
        float occlusion = (attenuation * (sin(horizon_angle) - sin(tangent_angle)));
        averaged_samples += occlusion;
    }

    // averaged_samples *= 0.03;

    averaged_samples /= num_radii;

    averaged_samples = pow(averaged_samples * 1.5, 1.0);

    result = vec4(1 - saturate(averaged_samples));
    // result = vec4(mid_nrm, 1);
}

