#version 420

#pragma include "Includes/Configuration.inc.glsl"

out vec4 result;

uniform samplerBuffer CommandQueue;
uniform layout(rgba32f) imageBuffer LightData;
uniform int commandCount;

// Command indices
#define CMD_INVALID 0
#define CMD_STORE_LIGHT 1
#define CMD_REMOVE_LIGHT 2

int readInt(inout int offset) {
    int val = int(texelFetch(CommandQueue, offset).x);
    offset += 1;
    return val;
}

vec4 readVec4(inout int offset) {
    vec4 val = vec4(
        texelFetch(CommandQueue, offset).x,
        texelFetch(CommandQueue, offset+1).x,
        texelFetch(CommandQueue, offset+2).x,
        texelFetch(CommandQueue, offset+3).x);
    offset += 4;
    return val;
}

void main() {


    int currentBufferOffs = 0;
    result = commandCount == 0 ? vec4(0, 1, 0, 1) : vec4(1, 0, 0, 1);

    // Process each command
    for (int commandIdx = 0; commandIdx < commandCount; commandIdx++) {

        currentBufferOffs = commandIdx * 32;

        int commandType = readInt(currentBufferOffs);

        // CMD_INVALID
        if (commandType == CMD_INVALID) {
            continue;

        // CMD_STORE_LIGHT
        } else if (commandType == CMD_STORE_LIGHT) {

            int slot = readInt(currentBufferOffs);

            vec4 data0 = readVec4(currentBufferOffs);
            vec4 data1 = readVec4(currentBufferOffs);
            vec4 data2 = readVec4(currentBufferOffs);
            vec4 data3 = readVec4(currentBufferOffs);

            int offs = slot * 4;
            imageStore(LightData, offs + 0, data0);
            imageStore(LightData, offs + 1, data1);
            imageStore(LightData, offs + 2, data2);
            imageStore(LightData, offs + 3, data3);

        // CMD_REMOVE_LIGHT
        } else if (commandType == CMD_REMOVE_LIGHT) {

            int slot = readInt(currentBufferOffs);
            int offs = slot * 4;
            imageStore(LightData, offs + 0, vec4(0));
            imageStore(LightData, offs + 1, vec4(0));
            imageStore(LightData, offs + 2, vec4(0));
            imageStore(LightData, offs + 3, vec4(0));
        }


    }

}