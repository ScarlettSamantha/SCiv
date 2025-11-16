#version 330 core

uniform sampler2D p3d_Texture0;
uniform vec4 uColor;
uniform float uOpacity;

in vec2 v_texcoord;
out vec4 o_color;

void main() {
    vec4 base = texture(p3d_Texture0, v_texcoord);
    float alpha = base.a * uOpacity;
    if (alpha <= 0.001) {
        discard;
    }

    vec3 rgb = mix(base.rgb, uColor.rgb, uColor.a);
    o_color = vec4(rgb, alpha);
}
