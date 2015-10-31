#version 150


uniform mat4 p3d_ModelViewProjectionMatrix;

in vec4 p3d_Vertex;

uniform sampler2D DatasetTex;
uniform isamplerBuffer DynamicStripsTex;

// uniform samplerBuffer DrawnObjectsTex;
uniform sampler2D DrawnObjectsTex;

out vec4 col;


void main() {
    
    int strip_offs = gl_InstanceID;
    int vtx_idx = gl_VertexID;

    ivec2 strip_data = texelFetch(DynamicStripsTex, strip_offs).xy;

    int object_id = strip_data.x;
    int strip_id = strip_data.y;

    // Read transform from object data
    int dobj_offs = 1 + 5 * object_id;

    vec4 mt0 = texelFetch(DrawnObjectsTex, ivec2(dobj_offs + 1, 0), 0).bgra;
    vec4 mt1 = texelFetch(DrawnObjectsTex, ivec2(dobj_offs + 2, 0), 0).bgra;
    vec4 mt2 = texelFetch(DrawnObjectsTex, ivec2(dobj_offs + 3, 0), 0).bgra;
    vec4 mt3 = texelFetch(DrawnObjectsTex, ivec2(dobj_offs + 4, 0), 0).bgra;

    mat4 transform = mat4(mt0, mt1, mt2, mt3); 

    // 2 for bounds, 1 for visibility
    int data_offs = 3 + vtx_idx * 2;

    vec4 data0 = texelFetch(DatasetTex, ivec2(data_offs, strip_id), 0).bgra;  
    vec4 data1 = texelFetch(DatasetTex, ivec2(data_offs + 1, strip_id), 0).bgra;

    vec4 vtx_pos = transform * vec4(data0.xyz, 1);

    col = vec4(vtx_pos);

    vec3 nrm = normalize(vec3(data0.w, data1.xy));
    col.xyz = nrm;

    gl_Position = p3d_ModelViewProjectionMatrix * vtx_pos;    

}
