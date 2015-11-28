#pragma once


#pragma include "Includes/Structures/LightData.struct.glsl"




#define LT_EMPTY 0
#define LT_POINT_LIGHT 1
#define LT_SPOT_LIGHT 2

/*

Description of the packing and the layout can be found here:
https://github.com/tobspr/RenderPipeline/wiki/LightStorage

*/


LightData read_light_data(samplerBuffer LightDataBuffer, int offset) {
    LightData data;
    data.Data0 = texelFetch(LightDataBuffer, offset + 0);
    data.Data1 = texelFetch(LightDataBuffer, offset + 1);
    data.Data2 = texelFetch(LightDataBuffer, offset + 2);
    data.Data3 = texelFetch(LightDataBuffer, offset + 3);
    return data;
}


int get_light_type(LightData data) {
    return int(data.Data0.x);
}

int get_ies_profile(LightData data) {
    return int(data.Data0.y);
}

vec3 get_light_position(LightData data) {
    return vec3(data.Data0.zw, data.Data1.x);
}

vec3 get_light_color(LightData data) {
    return data.Data1.yzw;
}




/*

Point Light dataset

*/

float get_pointlight_radius(LightData data) {
    return data.Data2.x;
}

float get_pointlight_inner_radius(LightData data) {
    return data.Data2.y;
}


/*

Spot Light dataset

*/

float get_spotlight_radius(LightData data) {
    return data.Data2.x;
}

float get_spotlight_fov(LightData data) {
    return data.Data2.y;
}

vec3 get_spotlight_direction(LightData data) {
    return vec3(data.Data2.zw, data.Data3.x);
}

