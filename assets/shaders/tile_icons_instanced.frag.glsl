#version 330

uniform sampler2D icon_atlas;
uniform float u_ring_radius;
uniform float u_icon_half;
uniform vec2  u_aniso;

in vec2 v_base_uv;
in vec4 v_pos_scale;
in vec4 v_uv0;
in vec4 v_uv1;
in vec4 v_uv2;
in vec4 v_uv3;
in vec4 v_uv4;
in vec4 v_uv5;
in vec4 v_uv6;
in vec2 v_local;

out vec4 o_color;

vec4 sample_rect(vec4 rect, vec2 xy, float half_size) {
    if (rect.z <= rect.x || rect.w <= rect.y) return vec4(0.0);
    vec2 p = (xy / half_size) * 0.5 + 0.5;
    if (any(greaterThan(abs(xy), vec2(half_size)))) return vec4(0.0);
    return texture(icon_atlas, mix(rect.xy, rect.zw, p));
}

vec2 ring(float deg) {
    float a = radians(deg);
    float k = v_pos_scale.w;
    vec2 p = vec2(cos(a), sin(a)) * (u_ring_radius * k);
    return p * u_aniso;
}

void main() {
    float s = u_icon_half * v_pos_scale.w;

    vec2 c_n  = ring( 90.0);
    vec2 c_ne = ring( 30.0);
    vec2 c_e  = ring(  0.0);
    vec2 c_se = ring(330.0);
    vec2 c_s  = ring(270.0);
    vec2 c_sw = ring(210.0);
    vec2 c_w  = ring(180.0);

    vec4 acc = vec4(0.0);
    acc += sample_rect(v_uv0, v_local - c_n , s);
    acc += sample_rect(v_uv1, v_local - c_ne, s);
    acc += sample_rect(v_uv2, v_local - c_e , s);
    acc += sample_rect(v_uv3, v_local - c_se, s);
    acc += sample_rect(v_uv4, v_local - c_s , s);
    acc += sample_rect(v_uv5, v_local - c_sw, s);
    acc += sample_rect(v_uv6, v_local - c_w , s);

    o_color = vec4(acc.rgb, clamp(acc.a, 0.0, 1.0));
}