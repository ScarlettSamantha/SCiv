#version 130

in vec2 texcoord;
uniform vec4 borderColor;
uniform int  edgeMask;    // bit 0..5 → the 6 sides of the hex
out vec4 fragColor;

const float HEX_RADIUS = 0.5;

// distance from p to segment a–b; also returns length along the segment in projLen
float distToSegment(vec2 p, vec2 a, vec2 b, out float projLen) {
    vec2 ba = b - a;
    vec2 pa = p - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    projLen = h * length(ba);
    return length(pa - ba * h);
}

// flat-top hex corners, centered at (0.5,0.5)
vec2 hex_corner(float angleDeg) {
    float rad = radians(angleDeg);
    return vec2(0.5) + vec2(cos(rad), sin(rad)) * HEX_RADIUS;
}

void main() {
    // how “thick” in UV‐space we want the line:
    float thickness = 0.02;
    float proj;
    bool drawEdge = false;

    // loop the 6 sides; only draw ones whose bit is set in edgeMask
    for (int i = 0; i < 6; ++i) {
        if (((edgeMask >> i) & 1) == 0) 
            continue;

        float baseAng = -30.0 + 60.0 * i;
        vec2 a = hex_corner(baseAng);
        vec2 b = hex_corner(baseAng + 60.0);
        // Only draw if the borderColor is red (R==1, G==0, B==0)
        if (borderColor.r < 0.99 || borderColor.g > 0.01 || borderColor.b > 0.01)
            discard;
        float d = distToSegment(texcoord, a, b, proj);
        if (d < thickness) {
            drawEdge = true;
            break;
        }
    }

    if (!drawEdge) 
        discard;

    fragColor = borderColor;
}
