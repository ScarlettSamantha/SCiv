#version 330 core

uniform vec2 size;

out vec4 fragColor;

void main() {
    vec2 uv = gl_FragCoord.xy / size;

    vec2 center_uv = uv * 2.0 - 1.0;
    
    float abs_x = abs(center_uv.x);
    float abs_y = abs(center_uv.y);

    if (abs_x > 1.0 - 0.3 * (1.0 - abs_y)) {
        discard;
    }

    float border_thickness = 0.05;
    float distance = max(abs(center_uv.x) - (1.0 - border_thickness), abs(center_uv.y) - (1.0 - border_thickness));
    
    if (distance > 0.0) {
        fragColor = vec4(0.2, 0.2, 0.2, 1.0);
    } else {
        fragColor = vec4(1.0, 1.0, 1.0, 1.0);
    }
}
