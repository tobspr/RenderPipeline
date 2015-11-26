#version 420

#pragma include "Includes/Configuration.inc.glsl"

out vec4 result;

uniform samplerBuffer CommandQueue;
uniform layout(rgba32f) imageBuffer LightData;
uniform int commandCount;

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

        // 0 - Invalid Command
        if (command_type == CMD_invalid) {
            continue;

        // 1 - Store Light
        } else if (command_type == CMD_store_light) {

            int slot = readInt(read_ptr);
            int offs = slot * 4;

            for (int i = 0; i < 4; ++i) {
                // Just copy the data over
                imageStore(LightData, offs + i, readVec4(read_ptr));
            }

        // 2 - Remove Light
        } else if (command_type == CMD_remove_light) {

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