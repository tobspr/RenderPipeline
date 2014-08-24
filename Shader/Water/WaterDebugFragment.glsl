#version 400
out vec3 color;
in vec2 texcoord;
in vec2 origTexcoord;
uniform sampler2D displacement;
uniform sampler2D normal;


void main() {

    vec3 sun = normalize(vec3(1));

    vec3 displace = texture(displacement, texcoord).xyz;
    vec3 displaceNormal = texture(normal, texcoord).xyz;
    float fresnel = max(0.2, dot(displaceNormal, sun));
    vec3 diffuse = vec3(0.3,0.6,0.9) * fresnel;

    color = vec3(diffuse.xyz);
}