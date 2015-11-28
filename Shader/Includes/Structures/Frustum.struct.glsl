#pragma once


struct Frustum {
    vec4 left;
    vec4 right;
    vec4 top;
    vec4 bottom;

    vec4 nearPlane;
    vec4 farPlane;

};