

#define saturate(v) clamp(v, 0, 1)

#define M_PI 3.14159265359
#define HALF_PI 1.57079632679
#define TWO_PI 6.28318530718



// Fixes the cubemap direction
vec3 fix_cubemap_coord(vec3 coord) {
    return normalize(coord.xzy * vec3(1,-1,1));
}


vec3 get_cubemap_coordinate(int face_index, vec2 coord) {
    vec3 baseDir = vec3(0);
    if (face_index == 0) baseDir = vec3(1.0, -coord.y, -coord.x);
    else if (face_index == 1) baseDir = vec3(-1.0, -coord.y, coord.x);
    else if (face_index == 2) baseDir = vec3(coord.x, 1.0, coord.y);
    else if (face_index == 3) baseDir = vec3(coord.x, -1.0, -coord.y);
    else if (face_index == 4) baseDir = vec3(coord.x, -coord.y, 1.0);
    else if (face_index == 5) baseDir = vec3(-coord.x, -coord.y, -1.0);
    return normalize(baseDir);
}


vec2 get_skydome_coord(vec3 view_dir) {
    float angle = (atan(view_dir.x, view_dir.y) + M_PI) / (2.0 * M_PI);
    return vec2(angle, view_dir.z);
}


// Converts a coordinate like "gl_FragCoord" to a cubemap direction, with a given
// cubemap size. Assumes the render target has a size of (6 * cubemap_size, cubemap_size).
// clamped_coord will contain a coordinate from (0 .. cubemap_size), this can be
// used for further processing or writing the result. 
// face will contain the selected cubemap face.
vec3 texcoord_to_cubemap(int cubemap_size, ivec2 coord, out ivec2 clamped_coord, out int face) {
    face = coord.x / cubemap_size;
    clamped_coord = coord % cubemap_size;
    vec2 local_coord = saturate( (clamped_coord+0.5) / float(cubemap_size)) * 2.0 - 1.0;
    return get_cubemap_coordinate(face, local_coord);
}

// Version of texcoord_to_cubemap without the out parameters
vec3 texcoord_to_cubemap(int cubemap_size, ivec2 coord) {
    ivec2 clamped_coord; int face;
    return texcoord_to_cubemap(cubemap_size, coord, clamped_coord, face);
}

