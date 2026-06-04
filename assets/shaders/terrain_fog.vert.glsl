#version 330 core

layout(location = 0) in vec4 p3d_Vertex;
layout(location = 1) in vec2 p3d_MultiTexCoord0;

out vec2 v_uv;

uniform mat4 p3d_ModelViewProjectionMatrix;

void main() {
    v_uv = p3d_MultiTexCoord0 * 2.0 - 1.0;
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
}
