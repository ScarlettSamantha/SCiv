#version 130

uniform vec2 size; // width, height

out vec4 fragColor;

void main() {
    vec2 uv = gl_FragCoord.xy / size;

    // Centered UV
    vec2 center_uv = uv * 2.0 - 1.0;
    
    // Calculate "rounded hexplate" distance
    float abs_x = abs(center_uv.x);
    float abs_y = abs(center_uv.y);

    // Arrow sides logic (kinda diamond with cutoff)
    if (abs_x > 1.0 - 0.3 * (1.0 - abs_y)) {
        discard; // outside the arrow points
    }

    // Border
    float border_thickness = 0.05;
    float distance = max(abs(center_uv.x) - (1.0 - border_thickness), abs(center_uv.y) - (1.0 - border_thickness));
    
    if (distance > 0.0) {
        fragColor = vec4(0.2, 0.2, 0.2, 1.0); // Dark border color
    } else {
        fragColor = vec4(1.0, 1.0, 1.0, 1.0); // Inner white color
    }
}
