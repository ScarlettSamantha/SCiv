#version 330 core

in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec4 p3d_Color;
uniform mat4 p3d_ModelViewProjectionMatrix;
out vec3 v_normal;
out vec4 v_color;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    v_normal = normalize(p3d_Normal);
    v_color = p3d_Color;
}