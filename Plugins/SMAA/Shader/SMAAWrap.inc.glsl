#pragma once

// This file just sets a few defines and then includes the SMAA header

#pragma include "Includes/Configuration.inc.glsl"

#define SMAA_GLSL_4
#define SMAA_RT_METRICS vec4(1.0 / WINDOW_WIDTH, 1.0 / WINDOW_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT)

// Get seleted SMAA quality
#if ENUM_V_ACTIVE(SMAA, smaa_quality, low)
    #define SMAA_PRESET_LOW
#elif ENUM_V_ACTIVE(SMAA, smaa_quality, medium)
    #define SMAA_PRESET_MEDIUM
#elif ENUM_V_ACTIVE(SMAA, smaa_quality, high)
    #define SMAA_PRESET_HIGH
#elif ENUM_V_ACTIVE(SMAA, smaa_quality, ultra)
    #define SMAA_PRESET_ULTRA
#else
    #error Unkown smaa quality value!
#endif


// Include both Pixel and Vertex shader, because we do the vertex shader logic
// in the pixel shader.
#define SMAA_INCLUDE_VS 1
#define SMAA_INCLUDE_PS 1

// Optionally enable smaa predication
#define SMAA_PREDICATION 1
#define SMAA_PREDICATION_SCALE 3.0
#define SMAA_PREDICATION_THRESHOLD 0.00001

// SMAA defines its own saturate, make sure we don't run into conflicts
#ifdef saturate
    #undef saturate
#endif

// Include the actual smaa header
#pragma include "SMAA.inc.glsl"

