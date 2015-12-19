#pragma once
#pragma include "Includes/Structures/LightData.struct.glsl"

/*

Description of the packing and the layout can be found here:
https://github.com/tobspr/RenderPipeline/wiki/LightStorage

*/

// Reads the light data from a given buffer and offset
LightData read_light_data(samplerBuffer LightDataBuffer, int offset) {
    LightData data;
    data.Data0 = texelFetch(LightDataBuffer, offset + 0);
    data.Data1 = texelFetch(LightDataBuffer, offset + 1);
    data.Data2 = texelFetch(LightDataBuffer, offset + 2);
    data.Data3 = texelFetch(LightDataBuffer, offset + 3);
    return data;
}

// Extracts the type of a light
int get_light_type(LightData data) {
    return int(data.Data0.x);
}

// Extracts the ies profile index of a light
int get_ies_profile(LightData data) {
    return int(data.Data0.y);
}

// Extracts the light world space position
vec3 get_light_position(LightData data) {
    return vec3(data.Data0.zw, data.Data1.x);
}

// Extracts the light color
vec3 get_light_color(LightData data) {
    return data.Data1.yzw;
}




/*

Point Light Dataset

*/

// Extracts the radius of a point light
float get_pointlight_radius(LightData data) {
    return data.Data2.x;
}

// Extracts the inner radius of a point light
float get_pointlight_inner_radius(LightData data) {
    return data.Data2.y;
}


/*

Spot Light Dataset

*/

// Extracts the radius of a spot light
float get_spotlight_radius(LightData data) {
    return data.Data2.x;
}

// Extracts the fov of a spot light
float get_spotlight_fov(LightData data) {
    return data.Data2.y;
}

// Extracts the direction of a spot light
vec3 get_spotlight_direction(LightData data) {
    return vec3(data.Data2.zw, data.Data3.x);
}

