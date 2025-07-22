#version 330 core

in vec2 uv;
uniform float health_ratio;   // 0.0 → 1.0
uniform float border;         // e.g. 0.02
in vec4 color;

out vec4 fragColor;

void main() {
    // 1) outline
    if (uv.x < border || uv.x > 1.0 - border ||
        uv.y < border || uv.y > 1.0 - border) {
        fragColor = vec4(0.0, 0.0, 0.0, 0.9);
        return;
    }

    // 2) thin background band at top/bottom
    if (uv.y < 0.10 || uv.y > 0.90) {
        fragColor = vec4(0.0, 0.0, 0.0, 0.7);
        return;
    }

    // 3) fill region
    if (uv.x <= health_ratio) {
        vec3 col = mix(
            vec3(1.0, 0.0, 0.0),   // red
            vec3(0.0, 1.0, 0.0),   // green
            health_ratio
        );
        fragColor = vec4(col, 0.9);
    } else {
        discard;
    }

    // 4) apply color tint
    fragColor.rgb *= color.rgb;
    fragColor.a *= color.a;  // apply alpha from color
    fragColor.a = clamp(fragColor.a, 0.0, 1.0);  // ensure alpha is valid
    if (fragColor.a < 0.01) {
        discard;  // skip rendering if nearly transparent
    }
}
