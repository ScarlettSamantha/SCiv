#version 130

in vec3 v_normal;
in vec4 v_color;
out vec4 fragColor;

void main() {
    // top face if normal almost up
    if (v_normal.z > 0.99) {
        fragColor = v_color;
    } else {
        fragColor = vec4(1.0, 0.0, 1.0, 1.0);
    }
}