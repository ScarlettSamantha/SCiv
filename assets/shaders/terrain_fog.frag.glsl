#version 330 core

in vec2 v_uv;
out vec4 fragColor;

uniform vec4 fogColor;
uniform float hexRadius;
uniform float edgeSoftness;
uniform float fogStrength;

const float PI = 3.141592653589793;

float hexDist(vec2 p) {
    float k = sqrt(3.0);
    p = abs(p);
    return max(p.x * 0.5 + k * p.y * 0.5, p.x);
}

void main() {
    float a = PI / 6.0;
    vec2 uv = vec2(
        v_uv.x * cos(a) - v_uv.y * sin(a),
        v_uv.x * sin(a) + v_uv.y * cos(a)
    );

    uv /= hexRadius;

    float d = hexDist(uv);
    float softness = max(0.0001, edgeSoftness / hexRadius);
    float inside = 1.0 - smoothstep(1.0, 1.0 + softness, d);
    float edge = 1.0 - smoothstep(1.0 - softness, 1.0, d);
    vec3 rgb = mix(fogColor.rgb * 0.92, fogColor.rgb, edge);
    float alpha = fogColor.a * fogStrength * inside;

    if (alpha <= 0.0001) {
        discard;
    }

    fragColor = vec4(rgb, alpha);
}
