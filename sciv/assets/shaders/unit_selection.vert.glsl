#version 330 core

layout(location = 0) in vec4  p3d_Vertex;

out vec2 v_uv;
uniform float radius;
uniform mat4  p3d_ModelViewProjectionMatrix;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;

    v_uv = p3d_Vertex.xy / radius;
}