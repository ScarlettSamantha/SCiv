#version 130

in vec2 uv;
uniform sampler2D iconTex;
out vec4 fragColor;
void main() {
    vec4 c = texture(iconTex, uv);
    if (c.a < 0.1) discard;
    fragColor = c;
}