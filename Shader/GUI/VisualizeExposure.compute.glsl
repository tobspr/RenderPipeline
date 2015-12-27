#version 430

#pragma include "Includes/Configuration.inc.glsl"

layout(local_size_x = 10, local_size_y = 4, local_size_z = 1) in;

uniform writeonly image2D DestTex;
uniform samplerBuffer ExposureTex;

void main() {

    // TODO: Might make this an input
    const ivec2 widget_size = ivec2(140, 20);
    ivec2 coord = ivec2(gl_GlobalInvocationID.xy);
        
    // Store the current pixels color
    vec4 color = vec4(0, 0, 0, 0);
    vec4 border_color = vec4(0.9, 0.9, 0.9, 1.0);

    // Border
    const int border_size = 1;
    if (coord.x < border_size || coord.x >= widget_size.x - border_size ||
        coord.y < border_size || coord.y >= widget_size.y - border_size) {
        color += border_color * (1 - color.w);
    }

    // Fetch exposure settings
    const float factor = 12.0;
    float min_exp = make_logarithmic(GET_SETTING(ColorCorrection, min_exposure), factor);
    float max_exp = make_logarithmic(GET_SETTING(ColorCorrection, max_exposure), factor);
    
    // Fetch current exposure
    float curr_exposure = texelFetch(ExposureTex, 0).x;

    // Slider
    float slider_pos = (curr_exposure - min_exp) / (max_exp - min_exp);

    // Make visualization logarithmic
    slider_pos = make_logarithmic(slider_pos, 100.0);

    const int slider_w = 4;
    int slider_pos_int = int(slider_pos * float(widget_size.x - 2 * border_size)) + border_size;

    if (coord.x > slider_pos_int - slider_w && coord.x < slider_pos_int + slider_w) {
        // Don't draw the slider over the border
        color += vec4(27, 78, 129, 255.0) / 255.0 * (1 - color.w);
    }

    imageStore(DestTex, coord, color);
}
