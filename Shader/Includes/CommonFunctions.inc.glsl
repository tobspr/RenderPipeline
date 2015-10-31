

#define saturate(v) clamp(v, 0, 1)

#define M_PI 3.14159265359


// Fixes the cubemap direction
vec3 fix_cubemap_coord(vec3 coord) {
    return normalize(coord.xzy * vec3(1,-1,1));
}


vec3 get_cubemap_coordinate(int face_index, vec2 coord) {
    vec3 baseDir = vec3(0);
    const float unit_size = 1.0;
    if (face_index == 0) baseDir = vec3(unit_size, -coord.y, -coord.x);
    else if (face_index == 1) baseDir = vec3(-unit_size, -coord.y, coord.x);
    else if (face_index == 2) baseDir = vec3(coord.x, unit_size, coord.y);
    else if (face_index == 3) baseDir = vec3(coord.x, -unit_size, -coord.y);
    else if (face_index == 4) baseDir = vec3(coord.x, -coord.y, unit_size);
    else if (face_index == 5) baseDir = vec3(-coord.x, -coord.y, -unit_size);
    return normalize(baseDir);
}


vec2 get_skydome_coord(vec3 view_dir) {
    float angle = (atan(view_dir.x, view_dir.y) + M_PI) / (2.0 * M_PI);
    return vec2(angle, view_dir.z);
}
