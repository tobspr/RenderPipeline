#version 400

in vec3 worldpos;

void main() {
    // Simulate transparent shadows by using stochastic discard
    const float stepInterval = 0.05;
    // discard;
    if (mod(dot(worldpos, vec3(1)), stepInterval) > 0.5 * stepInterval ) discard;
}
