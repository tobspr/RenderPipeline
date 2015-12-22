#version 400
#pragma include "Includes/Configuration.inc.glsl"
#pragma include "Includes/ColorSpaces/ColorSpaces.inc.glsl"


uniform sampler2D ShadedScene;
out vec4 result;


float get_log_luminance(vec3 color) {
    float lum = get_luminance(color);
    return max(0.0, GET_SETTING(ColorCorrection, brightness_scale) * lum);
}

void main() {

    ivec2 coord_screen = ivec2(gl_FragCoord.xy) * 4;
    vec2 local_coord = (coord_screen+1.0) / SCREEN_SIZE;
    vec2 pixel_offset = 2.0 / SCREEN_SIZE;

    float lum0 = get_log_luminance(textureLod(ShadedScene, local_coord, 0).xyz);
    float lum1 = get_log_luminance(textureLod(ShadedScene, local_coord + vec2(pixel_offset.x, 0), 0).xyz);
    float lum2 = get_log_luminance(textureLod(ShadedScene, local_coord + vec2(0, pixel_offset.y), 0).xyz);
    float lum3 = get_log_luminance(textureLod(ShadedScene, local_coord + pixel_offset.xy, 0).xyz);

    result = vec4( (lum0 + lum1 + lum2 + lum3) * 0.25 );
}
