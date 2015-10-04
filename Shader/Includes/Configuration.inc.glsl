#pragma once


#define saturate(v) clamp(v, 0, 1)
#define M_PI 3.14159265359

#pragma include "$$PipelineTemp/ShaderAutoConfig.include"


// Fixes the cubemap direction
vec3 fix_cubemap_coord(vec3 coord) {
    return normalize(coord.xzy * vec3(1,-1,1));
}
