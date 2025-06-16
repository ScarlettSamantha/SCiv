// Vertex shader for the selection indicator
layout(location = 0) in vec4 p3d_Vertex;
uniform mat4 p3d_ModelViewProjectionMatrix;

void main() {
    // Transform vertex position to clip space
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
}