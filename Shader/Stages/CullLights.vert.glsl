#version 400

#pragma include "Includes/Configuration.inc.glsl"

uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
uniform isamplerBuffer CellListBuffer;

void main() {

    // Find the amount of cells to shade
    int num_total_cells = texelFetch(CellListBuffer, 0).x;

    // Compute the amount of pixel lines required to shade all cells
    int num_used_slices = int(ceil(float(num_total_cells) / LC_CULLING_SLICE_WIDTH));

    // Compute the percentage factor of the used slices
    float percentage_height = num_used_slices / float(LC_SHADE_SLICES);

    // Store the vertex position.
    gl_Position = vec4(p3d_Vertex.x, fma(fma(p3d_Vertex.z, 0.5, 0.5) * percentage_height, 2.0, -1.0) , 0, 1);
}
