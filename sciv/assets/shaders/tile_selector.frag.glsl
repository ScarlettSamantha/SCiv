#version 330 core

in vec2 v_uv;
out vec4 fragColor;

uniform float time;         // Panda3D will drive this
uniform float dashFreq;     // e.g. 12 segments around
uniform float pulseSpeed;   // how fast the “dash” moves
uniform float borderWidth;  // in normalized UV units (0.0–1.0)
uniform float hexRadius;    // = √3/2 ≈ 0.866
uniform vec4 color;         // RGBA color of the hexagon

const float PI = 3.141592653589793;

// compute distance to a hexagon edge
float hexDist(vec2 p) {
    float k = sqrt(3.0);
    p = abs(p);

    // this formula gives the “radius” of a point from hex center
    return max(p.x * 0.5 + k * p.y * 0.5, p.x);
}

void main() {
    // rotate by 30° to get flat-top orientation
    float a = PI / 6.0; 
    vec2 uv = vec2(
        v_uv.x * cos(a) - v_uv.y * sin(a),
        v_uv.x * sin(a) + v_uv.y * cos(a)
    );

    //  scale UVs by the flat-top radius so that at d==1 it fits the hexagon
    uv /= hexRadius;

    // now get distance to edge
    float d = hexDist(uv);

    // adjust borderWidth so it’s the same thickness
    float bw = borderWidth / hexRadius;
    float edge = smoothstep(1.0 - bw, 1.0, d)
               - smoothstep(1.0,       1.0 + bw, d);

    float ang = atan(v_uv.y, v_uv.x);
    float normAng = (ang + PI) / (2.0 * PI);
    float dash = step(0.3, fract(normAng * dashFreq - time * pulseSpeed));

    fragColor = vec4(color.rgb, edge * dash);
}
