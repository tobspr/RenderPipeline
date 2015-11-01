#pragma once

// This file just sets a few defines and then includes the SMAA header

#pragma include "Includes/Configuration.inc.glsl"

#define SMAA_GLSL_4
#define SMAA_RT_METRICS vec4(1.0 / WINDOW_WIDTH, 1.0 / WINDOW_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT)
#define SMAA_PRESET_ULTRA

#define SMAA_INCLUDE_VS 1
#define SMAA_INCLUDE_PS 1

// #define SMAA_PREDICATION 1

// SMAA defines its own saturate, make sure we don't run into conflicts
#ifdef saturate
#undef saturate
#endif

// Include the actual smaa header
#pragma include "SMAA.inc.glsl"
