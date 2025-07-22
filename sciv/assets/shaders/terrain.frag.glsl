#version 330 core

in vec2 uv0;
in vec2 uv1;
in vec2 uv2;

uniform sampler2D terrain_atlas;
uniform int       uv_index;

out vec4 fragColor;

void main() {
    vec2 uv = (uv_index == 0
               ? uv0
               : uv_index == 1
                 ? uv1
                 : uv2);

    fragColor = texture(terrain_atlas, uv);
}
