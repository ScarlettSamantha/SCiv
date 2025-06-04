#version 130

in vec4    p3d_Vertex;
in vec3    p3d_Normal;
in vec4    p3d_Color;
in vec2    p3d_MultiTexCoord0;

uniform mat4 p3d_ModelViewProjectionMatrix;

out vec3    v_normal;
flat out vec4 v_color;
out vec2    v_texcoord;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    v_normal   = normalize(p3d_Normal);
    v_color    = p3d_Color;
    v_texcoord = p3d_MultiTexCoord0;
}
