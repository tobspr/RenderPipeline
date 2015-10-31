#version 150

in vec4 col;
out vec4 result;

void main() {

    vec3 diff = vec3(0.6) * max(0, dot(col.xyz, normalize(vec3(0, 0.8, 1)))) + vec3(0.05);

    result.xyz = diff;
    result.w = 1.0;
}