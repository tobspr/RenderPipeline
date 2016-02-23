#version 430

%DEFINES%

#define IS_SHADOW_SHADER 1

#pragma include "render_pipeline_base.inc.glsl"
#pragma include "includes/vertex_output.struct.glsl"

%INCLUDES%
%INOUT%

layout(location=0) in VertexOutput vOutput;

#if OPT_ALPHA_TESTING
uniform sampler2D p3d_Texture0;
#endif

void main() {
    #if OPT_ALPHA_TESTING

        // Alpha tested shadows. This seems to be quite expensive, so we are
        // only doing this for the objects which really need it (like trees)
        float sampled_alpha = texture(p3d_Texture0, vOutput.texcoord).w;
        if (sampled_alpha < 0.1) discard;
    #endif

    %ALPHA_TEST%
}
