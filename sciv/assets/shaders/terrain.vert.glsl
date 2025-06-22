#version 140

// built-in Panda uniforms
uniform mat4 p3d_ModelViewProjectionMatrix;

// vertex inputs
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;  // UV set 0
in vec2 p3d_MultiTexCoord1;  // UV set 1
in vec2 p3d_MultiTexCoord2;  // UV set 2

// pass all three through to the fragment
out vec2 uv0;
out vec2 uv1;
out vec2 uv2;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    uv0 = p3d_MultiTexCoord0;
    uv1 = p3d_MultiTexCoord1;
    uv2 = p3d_MultiTexCoord2;
}
