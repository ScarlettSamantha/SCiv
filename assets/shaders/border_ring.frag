#version 130

in vec2 texcoord;
uniform vec4 borderColor; // Interpolated input color from vertex shader
out vec4 fragColor;

float distToSegment(vec2 p, vec2 a, vec2 b, out float projLen) {
    vec2 ba = b - a;
    vec2 pa = p - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    projLen = h * length(ba);
    return length(pa - ba * h);
}

const float PI = 3.1415926;
const float HEX_RADIUS = 0.5;

vec2 hex_corner(float angle_deg) {
    float rad = radians(angle_deg);
    return vec2(0.5) + vec2(cos(rad), sin(rad)) * HEX_RADIUS;
}

void main() {
    float thickness = 0.015;
    float dashLength = 0.08; // size of each dash segment
    float gapRatio = 0.5;    // fraction of each segment that is a gap

    bool visible = false;

    for (int i = 0; i < 6; ++i) {
        float base = -30.0 + 60.0 * i;

        vec2 a = hex_corner(base);
        vec2 b = hex_corner(base + 60.0);

        float projLen;
        float d = distToSegment(texcoord, a, b, projLen);

        if (d < thickness) {
            float pattern = mod(projLen, dashLength);
            if (pattern < dashLength * (1.0 - gapRatio)) {
                visible = true;
                break;
            }
        }
    }

    if (!visible) discard;

    fragColor = vec4(borderColor.rgb, 1.0); // Use interpolated input color
}