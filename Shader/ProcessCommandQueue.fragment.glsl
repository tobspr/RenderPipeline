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

    int read_ptr = 0;
    result = commandCount == 0 ? vec4(0, 1, 0, 1) : vec4(1, 0, 0, 1);

    // Process each command
    for (int command_index = 0; command_index < commandCount; command_index++) {

        read_ptr = command_index * 32;

        int command_type = readInt(read_ptr);

        // CMD_INVALID
        if (command_type == CMD_INVALID) {
            continue;

        // CMD_STORE_LIGHT
        } else if (command_type == CMD_STORE_LIGHT) {

            int slot = readInt(read_ptr);
            int offs = slot * 4;

            for (int i = 0; i < 4; ++i) {
                // Just copy the data over
                imageStore(LightData, offs + i, readVec4(read_ptr));
            }

        // CMD_REMOVE_LIGHT
        } else if (command_type == CMD_REMOVE_LIGHT) {

            int slot = readInt(read_ptr);
            int offs = slot * 4;

            // Just set the data to all zeroes
            for (int i = 0; i < 4; ++i) {
                imageStore(LightData, offs + i, vec4(0));               
            }
        }

        // .. further commands will follow

    }
}