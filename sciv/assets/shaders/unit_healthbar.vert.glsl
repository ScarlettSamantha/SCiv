#version 130

in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;         // card’s UVs from 0→1
uniform mat4 p3d_ModelViewProjectionMatrix;

out vec2 uv;
out vec4 color; 

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    uv = p3d_MultiTexCoord0;        // now true [0..1] in both axes
    color = vec4(1.0, 1.0, 1.0, 1.0); // default white color
}