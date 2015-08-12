#version 420

#pragma include "Includes/Configuration.include"
#pragma include "Includes/Structures/VertexOutput.struct"

#pragma ENTRY_POINT SHADER_IN_OUT

#if defined(USE_ALPHA_TEST) && defined(USE_ALPHA_TESTED_SHADOWS)

// Input from the vertex shader
layout(location=0) in ShadowVertexOutput vOutput;
uniform sampler2D p3d_Texture0;

#endif

void main() {

    #if defined(USE_ALPHA_TEST) && defined(USE_ALPHA_TESTED_SHADOWS)
        float alpha = texture(p3d_Texture0, vOutput.texcoord).a;
        if (alpha < 0.5) discard;
    #endif

    #pragma ENTRY_POINT SHADER_END
}
