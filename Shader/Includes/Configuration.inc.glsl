#pragma once

// #pragma optionNV (unroll all)


#pragma include "$$PipelineTemp/ShaderAutoConfig.include"



// Screen size macro
#define SCREEN_SIZE vec2(WINDOW_WIDTH, WINDOW_HEIGHT)
#define SCREEN_SIZE_INT ivec2(WINDOW_WIDTH, WINDOW_HEIGHT)


#define HAVE_PLUGIN(PLUGIN_NAME) ( HAVE_PLUGIN_ ## PLUGIN_NAME )

#pragma include "CommonFunctions.inc.glsl"

