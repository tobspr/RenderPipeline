#version 430

/*

SOURCE:
"Real Shading in Unreal Engine 4"
https://de45xmedrsdbp.cloudfront.net/Resources/files/2013SiggraphPresentationsNotes-26915738.pdf

*/


#define saturate(v) clamp(v, 0, 1)

#define M_PI 3.1415926535897932384626433
#define HALF_PI 1.5707963267948966192313216
#define TWO_PI 6.2831853071795864769252867
#define ONE_BY_PI 0.3183098861837906715377675

vec2 Hammersley(uint i, uint N)
{
  return vec2(
    float(i) / float(N),
    float(bitfieldReverse(i)) * 2.3283064365386963e-10
  );
}

vec3 ImportanceSampleGGX( vec2 E, float roughness )
{
    float m = roughness * roughness;
    float m2 = m * m;

    float Phi = 2 * M_PI * E.x;
    float CosTheta = sqrt( (1 - E.y) / ( 1 + (m2 - 1) * E.y ) );
    float SinTheta = sqrt( 1 - CosTheta * CosTheta );

    vec3 H;
    H.x = SinTheta * cos( Phi );
    H.y = SinTheta * sin( Phi );
    H.z = CosTheta;
    

    return vec3( H );
}

float brdf_visibility_smith(float roughness, float NxV, float NxL)
{
    float r_sq = roughness * roughness;
    float vis_v = NxL * ( NxV * ( 1 - r_sq ) + r_sq );
    float vis_l = NxV * ( NxL * ( 1 - r_sq ) + r_sq );
    return 0.5 / (vis_v + vis_l);
}

vec2 IntegrateBRDF( float roughness, float NxV )
{
    vec3 view_dir;
    view_dir.x = sqrt( 1.0f - NxV * NxV ); // sin
    view_dir.y = 0;
    view_dir.z = NxV; // cos
    float A = 0;
    float B = 0;
    const int sample_count = 8192 * 2;
    for( int i = 0; i < sample_count; i++ )
    {
        vec2 Xi = Hammersley( i, sample_count );
        {
            vec3 H = ImportanceSampleGGX( Xi, roughness );
            vec3 L = -reflect(view_dir, H);

            float NxL = saturate( L.z );
            float NxH = clamp(H.z, 0.0001, 1.0);
            float VxH = saturate( dot( view_dir, H ) );

            if( NxL > 0 )
            {
                float vis = brdf_visibility_smith( roughness, NxV, NxL );
                float factor = NxL * vis * (4.0 * VxH / NxH);
                float fresnel = pow(1.0 - VxH, 5.0);
                A += (1 - fresnel) * factor;
                B += fresnel * factor;
            }
        }
    }

    return vec2( A, B ) / sample_count;

}

layout(local_size_x=16, local_size_y=16) in;

uniform writeonly image2D Dest;

void main() {
    const int res = 256;
    ivec2 coord = ivec2(gl_GlobalInvocationID.xy);
    vec2 local_coord = (coord+0.5) / vec2(res);

    vec2 result = IntegrateBRDF(local_coord.y, local_coord.x);
    result = saturate(result);
    imageStore(Dest, coord, vec4(result, 0, 1));
}
