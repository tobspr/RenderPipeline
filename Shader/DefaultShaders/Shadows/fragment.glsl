#version 420

#pragma ENTRY_POINT SHADER_IN_OUT

#if defined(USE_ALPHA_TEST)
in vec2 texcoord;
uniform sampler2D p3d_Texture0;
#endif

void main() {

    #if defined(USE_ALPHA_TEST)
        float alpha = texture(p3d_Texture0, texcoord).a;
        if (alpha < 0.5) discard;

        // Testing
        // if (length(texture(p3d_Texture0, texcoord).xyz) < 0.0001) discard;
    #endif

    #pragma ENTRY_POINT SHADER_END
}
