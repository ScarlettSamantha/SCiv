#version 330 core

uniform mat4 p3d_ModelViewProjectionMatrix;

in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
in vec2 p3d_MultiTexCoord1;
in vec2 p3d_MultiTexCoord2;

out vec2 uv0;
out vec2 uv1;
out vec2 uv2;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    uv0 = p3d_MultiTexCoord0;
    uv1 = p3d_MultiTexCoord1;
    uv2 = p3d_MultiTexCoord2;
}
