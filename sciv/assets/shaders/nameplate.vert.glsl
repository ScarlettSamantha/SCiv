#version 330 core

uniform mat4 p3d_ModelViewProjectionMatrix;
uniform vec3 billboard_position;
uniform vec2 size; // width, height

void main() {
    vec2 corner = vec2(gl_VertexID & 1, (gl_VertexID >> 1) & 1);
    vec2 pos = (corner * 2.0 - 1.0) * size * 0.5;
    
    // Face the camera
    mat3 rot = mat3(
        normalize(vec3(p3d_ModelViewProjectionMatrix[0].xyz)),
        normalize(vec3(p3d_ModelViewProjectionMatrix[1].xyz)),
        normalize(vec3(p3d_ModelViewProjectionMatrix[2].xyz))
    );

    vec3 world_pos = billboard_position + rot * vec3(pos, 0.0);
    gl_Position = p3d_ModelViewProjectionMatrix * vec4(world_pos, 1.0);
}
