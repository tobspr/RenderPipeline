#version 430

/*

SOURCE:
"Real Shading in Unreal Engine 4"
https://de45xmedrsdbp.cloudfront.net/Resources/files/2013SiggraphPresentationsNotes-26915738.pdf

*/

#define saturate(a) clamp(a, 0, 1)
#define M_PI 3.14159265359

vec2 Hammersley(uint i, uint N)
{
  return vec2(
    float(i) / float(N),
    float(bitfieldReverse(i)) * 2.3283064365386963e-10
  );
}

vec4 ImportanceSampleGGX( vec2 E, float Roughness )
{
    float m = Roughness * Roughness;
    float m2 = m * m;

    float Phi = 2 * M_PI * E.x;
    float CosTheta = sqrt( (1 - E.y) / ( 1 + (m2 - 1) * E.y ) );
    float SinTheta = sqrt( 1 - CosTheta * CosTheta );

    vec3 H;
    H.x = SinTheta * cos( Phi );
    H.y = SinTheta * sin( Phi );
    H.z = CosTheta;
    
    float d = ( CosTheta * m2 - CosTheta ) * CosTheta + 1;
    float D = m2 / ( M_PI*d*d );
    float PDF = D * CosTheta;

    return vec4( H, PDF );
}


float Vis_SmithJointApprox( float Roughness, float NoV, float NoL )
{
    float a = Roughness * Roughness;
    float Vis_SmithV = NoL * ( NoV * ( 1 - a ) + a );
    float Vis_SmithL = NoV * ( NoL * ( 1 - a ) + a );
    return 0.5 / ( Vis_SmithV + Vis_SmithL );
}

vec2 IntegrateBRDF( float Roughness, float NoV )
{
    vec3 V;
    V.x = sqrt( 1.0f - NoV * NoV ); // sin
    V.y = 0;
    V.z = NoV; // cos
    float A = 0;
    float B = 0;
    const uint NumSamples = 1024;
    for( uint i = 0; i < NumSamples; i++ )
    {
        vec2 Xi = Hammersley( i, NumSamples );
        {
            vec3 H = ImportanceSampleGGX( Xi, Roughness ).xyz;
            vec3 L = 2 * dot( V, H ) * H - V;

            float NoL = saturate( L.z );
            float NoH = saturate( H.z );
            float VoH = saturate( dot( V, H ) );

            if( NoL > 0 )
            {
                float Vis = Vis_SmithJointApprox( Roughness, NoV, NoL );

                float a = Roughness * Roughness;
                float a2 = a*a;
                float Vis_SmithV = NoL * sqrt( NoV * (NoV - NoV * a2) + a2 );
                float Vis_SmithL = NoV * sqrt( NoL * (NoL - NoL * a2) + a2 );
                float NoL_Vis_PDF = NoL * Vis * (4 * VoH / NoH);

                float Fc = pow( 1 - VoH, 5 );
                A += (1 - Fc) * NoL_Vis_PDF;
                B += Fc * NoL_Vis_PDF;
            }
        }


    }

    return vec2( A, B ) / NumSamples;
}

layout(local_size_x=16, local_size_y=16) in;

uniform writeonly image2D Dest;

void main() {
    const int res = 256;
    ivec2 coord = ivec2(gl_GlobalInvocationID.xy);
    vec2 local_coord = coord / vec2(res);

    vec2 result = IntegrateBRDF(local_coord.y, local_coord.x);

    imageStore(Dest, coord, vec4(result, 0, 1));
}
