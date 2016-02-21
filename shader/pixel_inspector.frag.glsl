#version 400

in vec2 texcoord;
out vec4 color;
uniform sampler2D SceneTex;
uniform vec2 mousePos;

void main() {
    int border = 3;
    int zoom = 5;

    ivec2 int_coord = ivec2(texcoord * vec2(400, 300));
    if (int_coord.x < border || int_coord.y < border || int_coord.x >= 400 - border || int_coord.y >= 300 - border) {
        color = vec4(0.05, 0.05, 0.05, 1);
        return;
    }

    int_coord = (int_coord) / zoom - (ivec2(200, 150)) / zoom + ivec2(mousePos);
    color = texelFetch(SceneTex, int_coord, 0);
    color.w = 1.0;
}
