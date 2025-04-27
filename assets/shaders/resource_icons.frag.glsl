#version 130

uniform sampler2D icon_atlas;
uniform vec4 uv_rects[7];
uniform int icon_count;

in vec2 uv;
out vec4 fragColor;

void main() {
    vec4 color = vec4(0.0);

    vec2 local_uv;
    vec2 icon_uv;
    vec2 pos;
    vec2 size;
    vec4 sample;

    float main_offset_y = 0.0;
    float mini_offset_y = -0.35;

    for (int i = 0; i < icon_count; ++i) {
        if (i == 0) {
            // Main icon at top
            pos = vec2(0.5 - 1.0 / 6.0, 0.66 + main_offset_y);  // centered horizontally
            size = vec2(1.0 / 3.0, 1.0 / 3.0);                  // square region
        } else {
            // 2x3 grid of small icons below
            float col = float((i - 1) % 3);
            float row = float(2 - (i - 1) / 3);  // bottom row = 0
            pos = vec2(col / 3.0, row / 3.0 + mini_offset_y);
            size = vec2(1.0 / 3.0, 1.0 / 3.0);
        }

        local_uv = (uv - pos) / size;

        if (all(greaterThanEqual(local_uv, vec2(0.0))) &&
            all(lessThanEqual(local_uv, vec2(1.0)))) {
            
            vec4 rect = uv_rects[i];
            icon_uv = mix(rect.xy, rect.zw, local_uv);
            sample = texture(icon_atlas, icon_uv, -0.0);

            color = mix(color, sample, sample.a);
        }
    }

    // Discard fully transparent pixels (to avoid drawing base quad)
    if (color.a < 0.05)
        discard;

    fragColor = clamp(color, 0.0, 1.0);
}
