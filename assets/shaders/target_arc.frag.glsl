#version 330 core

uniform vec4  u_color;         
uniform float u_edge_feather; 

in float v_v;
out vec4 fragColor;

void main() {
    float edge = abs(v_v - 0.5) / 0.5;
    float alpha_edge = 1.0 - smoothstep(1.0 - u_edge_feather, 1.0, edge);

    float a = u_color.a * alpha_edge;
    if (a < 0.01) discard;

    fragColor = vec4(u_color.rgb, a);
}
