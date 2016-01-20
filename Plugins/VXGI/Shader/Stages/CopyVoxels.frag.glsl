#version 430

#pragma include "Includes/Configuration.inc.glsl"

uniform sampler3D SourceTex;
uniform writeonly image3D RESTRICT DestTex;

void main() {
    ivec2 coord_2d = ivec2(gl_FragCoord.xy);
    for (int z = 0; z < VOXEL_GRID_RES; ++z) {
        ivec3 coord = ivec3(coord_2d, z); 
        imageStore(DestTex, coord, texelFetch(SourceTex, coord, 0));
    }
}
