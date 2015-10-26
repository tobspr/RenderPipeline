
#version 430

layout(local_size_x=512, local_size_y=1, local_size_z=1) in;

// This shader takes the list of rendered objects with their transforms, 
// and spawns a strip for each rendered object

uniform samplerBuffer DrawnObjectsTex;

uniform isampler2D MappingTex;
uniform layout(r32i) iimageBuffer IndirectTex;
uniform layout(r32i) iimageBuffer DynamicStripsTex;
uniform sampler2D DatasetTex;

void main() {

    int thread_id = int(gl_GlobalInvocationID.x);

    int num_objects_drawn = int(texelFetch(DrawnObjectsTex, 0).x + 0.5);

    // Reset counter in the beginning

    if (thread_id == 0) {
        // imageStore(DynamicStripsTex, 0, ivec4(0));
        imageStore(IndirectTex, 0, ivec4(4096 * 3));
        imageStore(IndirectTex, 1, ivec4(1));
        imageStore(IndirectTex, 2, ivec4(0));
        imageStore(IndirectTex, 3, ivec4(1));
    }

    barrier();

    // For each drawn object
    if (thread_id < num_objects_drawn) {

        // Fetch the id of the object
        int read_offs = 1 + thread_id * 5;
        int object_id = int(texelFetch(DrawnObjectsTex, read_offs).x + 0.5);

        // Check out how many triangle strips the object has
        int num_strips = texelFetch(MappingTex, ivec2(0, object_id), 0).x;

        for (int k = 0; k < num_strips; ++k) {

            // Find the id of the triangle strip
            // Increase k by 1 since the first entry is the number of strips
            int strip_id = texelFetch(MappingTex, ivec2(k + 1, object_id), 0).x;

            // Find strip bounds
            vec3 strip_bb_min = texelFetch(DatasetTex, ivec2(0, strip_id), 0).xyz;
            vec3 strip_bb_max = texelFetch(DatasetTex, ivec2(1, strip_id), 0).xyz;

            if (strip_bb_min.z < 0.0) continue;

            // int offset = imageAtomicAdd(DynamicStripsTex, 0, 1) * 2;
            // imageAtomicAdd(IndirectTex, 0, 1);
            int offset = imageAtomicAdd(IndirectTex, 1, 1) * 2;

            imageStore(DynamicStripsTex, offset + 1, ivec4(thread_id));
            imageStore(DynamicStripsTex, offset + 2, ivec4(strip_id));
        }
    }
}
