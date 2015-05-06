#version 400

void main() {

    ivec2 coord = ivec2(gl_FragCoord.xy);

    if ( (coord.x+coord.y) % 5 == 0) discard;
}
