#version 430

layout (local_size_x = 16, local_size_y = 16) in;


layout(rgba16f) uniform image2D destination;
uniform sampler2DArray backfaceTex;
uniform sampler2DArray frontfaceTex;

uniform int gridSize;

const float solidMinAmount = 0.9;

vec2 getSolid(ivec3 coord, out vec4 resultFrontface, out vec4 resultBackface) {
    if (any(lessThan(coord, ivec3(0))) ||
        any(greaterThan(coord, ivec3(gridSize-1))) ) {
        return vec2(0.6);
    }

    resultBackface = texelFetch(backfaceTex, ivec3(coord), 0);
    resultFrontface = texelFetch(frontfaceTex, ivec3(coord), 0);
    return vec2(resultFrontface.w, resultBackface.w);
}

void main() {
    ivec2 texelCoords = ivec2(gl_GlobalInvocationID.xy);
    float stencil = 0.0;
    vec4 currentColor;
    for (int i = 0; i < gridSize; i++) {
        vec4 rf, rb;
        vec2 solidness = getSolid(ivec3(texelCoords, i), rf, rb);
        if (solidness.y > solidMinAmount) {
            stencil = 1.0;
            currentColor = rb;
        }
        if (solidness.x > solidMinAmount) {
            currentColor = rf;
        }


        imageStore(destination, texelCoords + ivec2(i*gridSize, 0), vec4(currentColor.xyz,stencil));

        if (solidness.x > solidMinAmount) {
        }
        stencil = 0.0;

        currentColor = vec4(0.5,0.5,0.5,1.0);

    }

    // now do the same from the other direction .. we don't know if the mesh has correct
    // walls
    stencil = 0.0;
    currentColor = vec4(0);

    for (int i = gridSize-1; i >= 0; i--) {
        vec4 rf, rb;
        vec2 solidness = getSolid(ivec3(texelCoords, i), rf, rb);
        
        if (solidness.x > solidMinAmount) {
            stencil = 1.0;
            currentColor = rf;
        }
        if (solidness.y > solidMinAmount) {
            currentColor = rb;
        }


        if (stencil > 0.5) {
            ivec2 coordsOld = texelCoords + ivec2(i*gridSize, 0);
            vec4 oldColor = imageLoad(destination, coordsOld);

            imageStore(destination, coordsOld, vec4( 
                (currentColor.xyz), stencil));
        }
        if (solidness.y > solidMinAmount) {
        }
        stencil = 0.0;
        
        currentColor = vec4(0.5,0.5,0.5,1.0);

    }


}