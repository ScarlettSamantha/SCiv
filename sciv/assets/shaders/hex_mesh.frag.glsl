#version 330 core

in vec3    v_normal;
flat in vec4 v_color;
in vec2    v_texcoord;

uniform sampler2D p3d_Texture0;

out vec4 fragColor;

void main() {
    if (v_normal.z > 0.95) {
        fragColor = texture(p3d_Texture0, v_texcoord);
    } else {
        // debug highlight for sides / walls
        fragColor = vec4(1.0, 0.0, 1.0, 1.0);
    }
}
