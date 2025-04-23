#version 130

in vec2 texcoord;
uniform vec4 borderColor;
uniform sampler2D borderMask;
uniform vec2 tilePos;
uniform vec2 mapSize;
uniform float time;

out vec4 fragColor;

const float PI = 3.1415926;
const float HEX_RADIUS = 0.5;

float distToSegment(vec2 p, vec2 a, vec2 b, out float projLen) {
    vec2 ba = b - a;
    vec2 pa = p - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    projLen = h * length(ba);
    return length(pa - ba * h);
}

vec2 hex_corner(float angle_deg) {
    float rad = radians(angle_deg);
    return vec2(0.5) + vec2(cos(rad), sin(rad)) * HEX_RADIUS;
}

void main() {
    vec2 tileUV = (tilePos + texcoord) / mapSize;
    vec3 maskColor = texture(borderMask, tileUV).rgb;

    float red = maskColor.r;
    float green = maskColor.g;

    if (red == 0.0 && green == 0.0) {
        discard;
    }

    float thickness = 0.015;
    float dashLength = 0.08;
    float gapRatio = 0.5;

    bool visible = false;
    bool isGreen = false;

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
                isGreen = (green > 0.0);
                break;
            }
        }
    }

    if (!visible) discard;

    vec3 finalColor = borderColor.rgb;

    if (isGreen) {
        float pulse = 0.5 + 0.5 * sin(time * 3.5);
        vec3 lightColor = mix(borderColor.rgb, vec3(1.0), 0.2);
        finalColor = mix(borderColor.rgb, lightColor, pulse);
    }

    fragColor = vec4(finalColor, 1.0);
}
